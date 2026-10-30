import unittest
from local_pass import explicit_suggestion, proposals
from bridge import harness

class BridgeTests(unittest.TestCase):
 def test_first_error_preserved_with_long_suffix(self):
  from diagnostics import bounded_feedback
  log='t.lean:3:4: error: unsolved goals\n⊢ False\n'+'x'*5000+'\nt.lean:20:1: warning: declaration uses sorry'
  feedback=bounded_feedback(log,100)
  self.assertEqual(feedback['first_error']['line'],3)
  self.assertIn('⊢ False',feedback['first_message'])
  self.assertTrue(feedback['truncated'])
  self.assertFalse(feedback['first_error']['goal_snapshot_trusted'])

 def test_repair_protocol_conversion(self):
  from protocol import repair_response_to_common
  import json
  converted=repair_response_to_common({'status':'candidate','proof_body':'by rfl','explanation':'ok'})
  self.assertEqual(json.loads(converted['content']),{'proof':'by rfl'})
  self.assertEqual(repair_response_to_common({'status':'need_context'})['kind'],'control')
  with self.assertRaises(ValueError):repair_response_to_common({'status':'candidate','proof_body':None})

 def test_ambiguous_query_not_accepted(self):
  self.assertIsNone(explicit_suggestion('Try this: exact a\nTry this: exact b'))
 def test_sorry_not_accepted(self):
  self.assertIsNone(explicit_suggestion('Try this: exact sorry'))
 def test_query_must_match_source_location(self):
  log='x.lean:10:2: info: Try this: exact h\nx.lean:22:2: info: Try this: exact z'
  self.assertEqual(explicit_suggestion(log,10),'exact h')
  self.assertIsNone(explicit_suggestion(log,11))
 def test_only_proof_field_allowed(self):
  raw={'choices':[{'message':{'content':'{"proof":"by rfl","statement":"False"}'}}],'usage':{'cost':0}}
  with self.assertRaises(ValueError):harness.parse_proof(raw,{'statement':'theorem t : True'},100)
 def test_repairs_preserve_prefix(self):
  for _,proof,_,_ in proposals('by\n  induction h',False):self.assertTrue(proof.startswith('by\n  induction h\n'))
 def test_score_does_not_choose_shorter_expensive_proof(self):
  base={'tokens':100,'raw_heartbeats':100}
  def result(t,h):return {'valid':True,'tokens':t,'environments':{'fixed':{'valid':True,'runs':[{'measurement':{'raw':h}}]}}}
  original=harness.candidate('original',result(100,100),base)
  costly=harness.candidate('short',result(50,200),base)
  self.assertLess(harness.ranking(original),harness.ranking(costly))
if __name__=='__main__':unittest.main()
