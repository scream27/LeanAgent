import json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tests'))
import resume as engine
from test_harness import FakeEvaluator
class Fake(FakeEvaluator):
 def evaluate(self,*a,**k):
  r=super().evaluate(*a,**k)
  for env in r['environments'].values():
   for sample in env['runs']:
    if 'measurement' in sample:sample['measurement']['axioms']=[]
  return r
class ResumeTests(unittest.TestCase):
 def test_three_independent_process_style_ticks_preserve_feedback(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);here=root/'experiments/live';d=here/'inputs/1';d.mkdir(parents=True)
   repo=engine.REPO;c=engine.harness.read(repo/'configs/smoke.json')
   for key in ('problem','template','project','prompt'):c[key]=str((repo/'configs'/c[key]).resolve())
   c['model']={'backend':'external','id':'test','exchange_directory':str(root/'runs/live-practice-2026-10-28/1/exchange'),'timeout_seconds':10}
   (d/'config.json').write_text(json.dumps(c));(d/'environment.json').write_text(json.dumps({'project':'unused'}))
   with patch.object(engine,'REPO',root),patch.object(engine,'HERE',here),patch.object(engine,'V2Evaluator',side_effect=lambda _:Fake()):
    for step,proof in enumerate(['by exact False.elim (by assumption)','by rfl','by rfl'],1):
     engine.resume(1)
     folder=root/'runs/live-practice-2026-10-28/1/exchange-v2'/f'{step:03}';p=json.loads((folder/'request.json').read_text());packet=json.loads(p['request']['messages'][1]['content'])
     if step==2:self.assertFalse(packet['latest']['feedback']['valid'])
     if step==3:self.assertTrue(packet['latest']['feedback']['valid'])
     (folder/'reply.json').write_text(json.dumps({'request_sha256':p['request_sha256'],'content':json.dumps({'proof':proof})}))
    engine.resume(1)
    raw=root/'runs/live-practice-2026-10-28/1/raw-v2'
    s=engine.harness.read(raw/'summary.json');self.assertTrue(s['final_valid']);self.assertEqual(s['state']['calls'],3)
    self.assertTrue(engine.harness.replay(raw)['record_replay_passed'])
if __name__=='__main__':unittest.main()
