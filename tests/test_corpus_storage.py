"""Exercise storage boundaries with small bundles, without Lean or network access."""
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import tarfile
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import corpus


def digest(value):
    return hashlib.sha256(value).hexdigest()


class CorpusStorageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=os.environ['PROJECT_CACHE_DIR'])
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.folder = self.root / 'data/corpora/sample/revision'
        self.folder.mkdir(parents=True)
        self.context = b'theorem original : True := by trivial\n'
        self.row = dict(id='sample-1', src=self.context.decode(), statement='theorem original : True',
                        proof='by trivial', context_file='context/Main.lean',
                        file_sha256=digest(self.context), src_sha256=digest(self.context),
                        proof_sha256=digest(b'by trivial'), problem_dir='problems/sample-1')
        with gzip.open(self.folder / 'inventory.jsonl.gz', 'wt') as f:
            f.write(json.dumps(self.row) + '\n')
        with tarfile.open(self.folder / 'context.tar.gz', 'w:gz') as tar:
            member = tarfile.TarInfo('context/Main.lean')
            member.size = len(self.context)
            tar.addfile(member, io.BytesIO(self.context))
        (self.folder / 'environment').mkdir()
        (self.folder / 'environment/lean-toolchain').write_text('leanprover/lean4:v4.26.0\n')
        (self.folder / 'subsets').mkdir()
        for name, rows in {'empty': [], 'verified': [{'id': 'sample-1', 'annotations': {'verified': True}}]}.items():
            with gzip.open(self.folder / f'subsets/{name}.jsonl.gz', 'wt') as f:
                for row in rows:
                    f.write(json.dumps(row) + '\n')
        self.manifest = dict(revision='revision',
            inventory={'path': 'inventory.jsonl.gz', 'sha256': corpus.sha(self.folder / 'inventory.jsonl.gz')},
            context={'sha256': corpus.sha(self.folder / 'context.tar.gz')},
            subsets={name: {'path': f'subsets/{name}.jsonl.gz',
                           'sha256': corpus.sha(self.folder / f'subsets/{name}.jsonl.gz')}
                     for name in ['empty', 'verified']},
            artifact_hashes={p.relative_to(self.folder).as_posix(): corpus.sha(p)
                             for p in self.folder.rglob('*') if p.is_file()})
        self.save_manifest()
        self.output = self.root / 'input'
        (self.root / 'runs').mkdir()
        (self.root / 'runs/secret-candidate.lean').write_text('private candidate')

    def save_manifest(self):
        (self.folder / 'manifest.json').write_text(json.dumps(self.manifest))
        (self.root / 'data/catalog.json').write_text(json.dumps({'corpora': {'sample': {
            'path': 'data/corpora/sample/revision',
            'manifest_sha256': corpus.sha(self.folder / 'manifest.json')}}}))

    def test_selection_contains_original_input_and_no_run_results(self):
        result = corpus.materialize('sample', ['sample-1'], self.output, self.root)
        self.assertEqual((self.output / 'problems/sample-1/reference.lean').read_bytes(), self.context)
        self.assertEqual((self.output / 'context/Main.lean').read_bytes(), self.context)
        self.assertFalse((self.output / 'runs').exists())
        self.assertEqual(len(result['files']), 6)
        for name, expected in result['files'].items():
            self.assertEqual(corpus.sha(self.output / name), expected)

    def test_unlisted_environment_files_are_not_included(self):
        (self.folder / 'environment/unlisted.txt').write_text('not part of the manifest')
        corpus.materialize('sample', ['sample-1'], self.output, self.root)
        self.assertFalse((self.output / 'environment/unlisted.txt').exists())

    def test_dangling_output_symlink_is_never_overwritten(self):
        self.output.symlink_to(self.root / 'missing')
        with self.assertRaises(FileExistsError):
            corpus.materialize('sample', ['sample-1'], self.output, self.root)
        self.assertTrue(self.output.is_symlink())

    def test_existing_output_is_never_overwritten(self):
        self.output.mkdir()
        (self.output / 'keep').write_text('keep')
        with self.assertRaises(FileExistsError):
            corpus.materialize('sample', ['sample-1'], self.output, self.root)
        self.assertEqual((self.output / 'keep').read_text(), 'keep')

    def test_unknown_id_and_duplicates_leave_no_output(self):
        for ids in [['missing'], ['sample-1', 'sample-1']]:
            with self.assertRaises(ValueError):
                corpus.materialize('sample', ids, self.output, self.root)
            self.assertFalse(self.output.exists())

    def test_tampered_inventory_and_environment_are_rejected(self):
        for relative in ['inventory.jsonl.gz', 'environment/lean-toolchain']:
            p = self.folder / relative
            original = p.read_bytes()
            p.write_bytes(original + b'changed')
            with self.assertRaises(ValueError):
                corpus.materialize('sample', ['sample-1'], self.output, self.root)
            self.assertFalse(self.output.exists())
            p.write_bytes(original)

    def test_canonical_directory_cannot_be_output(self):
        with self.assertRaises(ValueError):
            corpus.materialize('sample', ['sample-1'], self.root / 'data/new', self.root)

    def test_empty_subset_and_annotations(self):
        self.assertEqual(list(corpus.selected_rows(self.folder, self.manifest, [], 'empty')), [])
        row, annotations = next(corpus.selected_rows(self.folder, self.manifest, [], 'verified'))
        self.assertEqual(row, self.row)
        self.assertEqual(annotations, {'verified': True})

    def test_manifest_tampering_is_rejected(self):
        (self.folder / 'manifest.json').write_text('{}')
        with self.assertRaises(ValueError):
            corpus.load('sample', self.root)

    def test_archive_rejects_traversal_and_links(self):
        for name, link in [('../escaped', False), ('/absolute', False), ('link', True)]:
            archive = self.root / 'bad.tar.gz'
            with tarfile.open(archive, 'w:gz') as tar:
                member = tarfile.TarInfo(name)
                if link:
                    member.type = tarfile.SYMTYPE
                    member.linkname = '/tmp'
                tar.addfile(member)
            with self.assertRaises(ValueError):
                corpus.safe_unpack(archive, self.root / 'extract')
        self.assertFalse((self.root / 'escaped').exists())

    def test_resolve_rejects_external_symlink(self):
        (self.root / 'link').symlink_to(self.root.parent, target_is_directory=True)
        with self.assertRaises(ValueError):
            corpus.resolve(self.root, 'link/outside')


if __name__ == '__main__':
    unittest.main()
