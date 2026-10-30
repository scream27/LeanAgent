import unittest,json,hashlib
from pathlib import Path
from run import compatible_render,ORIGINAL_RENDER,HERE
class AdapterTests(unittest.TestCase):
 def test_normal_source_unchanged(self):
  for n in (4,5,6):
   p=json.loads((HERE/'inputs'/str(n)/'problem.json').read_text());t=(HERE/'inputs'/str(n)/'context.lean.in').read_text()
   self.assertEqual(compatible_render(t,p['reference'],p['name'],None),ORIGINAL_RENDER(t,p['reference'],p['name'],None))
 def test_measurement_keeps_declaration(self):
  for n in (4,5,6):
   p=json.loads((HERE/'inputs'/str(n)/'problem.json').read_text());t=(HERE/'inputs'/str(n)/'context.lean.in').read_text()
   a=compatible_render(t,p['reference'],p['name'],'test');b=ORIGINAL_RENDER(t,p['reference'],p['name'],'test')
   self.assertIn(p['reference'],a)
   self.assertEqual(len(a),len(b))
   self.assertEqual(sum(x!=y for x,y in zip(a,b)),int(n == 4))
 def test_frozen_candidates_unchanged(self):
  for path,digest in json.loads((HERE/'candidate-freeze.json').read_text())['sha256'].items():
   self.assertEqual(hashlib.sha256((HERE/path).read_bytes()).hexdigest(),digest,path)
if __name__=='__main__':unittest.main()
