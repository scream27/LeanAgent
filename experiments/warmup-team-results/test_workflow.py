import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
def module(name):
    spec=importlib.util.spec_from_file_location(name,HERE/(name+'.py'))
    loaded=importlib.util.module_from_spec(spec);spec.loader.exec_module(loaded);return loaded
collect=module('collect')
verify=module('verify')
export=module('export')

class WorkflowTests(unittest.TestCase):
    def test_import_integrity_and_scope(self):
        manifest=json.loads((HERE/'manifest.json').read_text())
        self.assertEqual([p['id'] for p in manifest['problems']],list(range(1,16)))
        for p in manifest['problems']:
            ids=set()
            for c in p['candidates']:
                self.assertNotIn(c['id'],ids);ids.add(c['id'])
                path=ROOT/c['path']
                self.assertEqual(collect.digest(path.read_bytes()),c['sha256'])
                source=next(path.parent.glob('source.*'))
                self.assertEqual(collect.digest(source.read_bytes()),c['sourceSha256'])
            self.assertIn(p['representativeId'], ids if ids else {None})
    def test_helpers_are_preserved_not_silently_dropped(self):
        proof=(HERE/'candidates/P12/손지연-final/candidate.lean').read_text()
        self.assertIn('tensor_gap_succ',proof)
        self.assertGreater(proof.count('lemma ')+proof.count('theorem '),1)
    def test_original_fallback_is_not_a_candidate(self):
        data=json.loads((HERE/'manifest.json').read_text())
        self.assertEqual(data['problems'][10]['candidates'],[])
    def test_unique_context_and_command_wrapper_guard(self):
        meta={'src':'theorem x : True := by trivial'}
        with self.assertRaises(ValueError):verify.template(meta,meta['src']*2)
        context,lead=verify.template(meta,'import Lean\nomit a in\n'+meta['src'])
        self.assertEqual(lead,'omit a in\n')
        out,_=verify.template(meta,'import Lean\n'+meta['src'])
        self.assertEqual(out.count('{{DECLARATION}}'),1)
    def test_prior_declarations_are_never_included_in_measured_target(self):
        meta={'src':'theorem target : True := by trivial'}
        source='import Lean\nnamespace Example\n@[simp]\nlemma earlier : True := by trivial\n\n/-- Target doc. -/\n'+meta['src']+'\nend Example'
        context,lead=verify.template(meta,source)
        self.assertEqual(lead,'/-- Target doc. -/\n')
        self.assertLess(context.index('{{HARNESS_COMMANDS}}'),context.index('namespace Example'))
        self.assertIn('lemma earlier',context)
        self.assertNotIn('lemma earlier',lead)
    def test_module_doc_does_not_capture_an_earlier_declaration(self):
        meta={'src':'theorem target : True := by trivial'}
        source='import Lean\n/-- Earlier doc. -/\ndef previous := 1\n/-! Section heading. -/\n'+meta['src']
        context,lead=verify.template(meta,source)
        self.assertEqual(lead,'')
        self.assertIn('def previous',context)
        self.assertIn('/-! Section heading. -/',context)
        self.assertIsNone(verify.trailing_doc_start(source.split(meta['src'])[0]))
        self.assertEqual(verify.trailing_doc_start('x\n/-- outer /- nested -/ doc -/\n'),2)
    def test_incomplete_run_cannot_publish(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp);(path/'summary.json').write_text('{}')
            with self.assertRaisesRegex(ValueError,'still running'):export.export(path,path/'out')
            self.assertFalse((path/'out').exists())

if __name__=='__main__':unittest.main()
