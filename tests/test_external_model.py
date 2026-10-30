import json,threading,time,unittest,tempfile
from pathlib import Path
from lean_agent import models,harness
from test_harness import FakeEvaluator,REPO

class ExternalTests(unittest.TestCase):
 def test_feedback_loop_and_replay(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);c=harness.read(REPO/'configs/smoke.json')
   for k in ('problem','template','project','prompt'):c[k]=str((REPO/'configs'/c[k]).resolve())
   c['model']={'backend':'external','id':'conversation-model','exchange_directory':str(root/'exchange'),'timeout_seconds':10}
   cfg=root/'config.json';cfg.write_text(json.dumps(c));errors=[];packets=[]
   def responder():
    try:
     for i,proof in enumerate(['by exact False.elim (by assumption)','by rfl','by rfl'],1):
      path=root/'exchange'/f'{i:03}'/'request.json';end=time.monotonic()+10
      while not path.exists():
       if time.monotonic()>end:raise TimeoutError()
       time.sleep(.01)
      p=json.loads(path.read_text());packets.append(json.loads(p['request']['messages'][1]['content']))
      (path.parent/'reply.json').write_text(json.dumps({'request_sha256':p['request_sha256'],'content':json.dumps({'proof':proof})}))
    except Exception as e:errors.append(e)
   t=threading.Thread(target=responder);t.start()
   s=harness.run(cfg,root/'run',evaluator=FakeEvaluator());t.join()
   self.assertEqual(errors,[]);self.assertFalse(packets[1]['latest']['feedback']['valid'])
   self.assertTrue(packets[2]['latest']['feedback']['valid']);self.assertEqual(s['backend'],'external')
   self.assertEqual(s['state']['calls'],3);self.assertTrue(harness.replay(root/'run')['record_replay_passed'])
 def test_timeout_has_no_invented_tokens(self):
  with tempfile.TemporaryDirectory() as tmp:
   r=models.query({},dict(backend='external',id='test',exchange_directory=tmp,timeout_seconds=.02),1)
   self.assertEqual(r['transport_error'],'ExternalReplyTimeout');self.assertNotIn('prompt_tokens',r['usage'])
if __name__=='__main__':unittest.main()
