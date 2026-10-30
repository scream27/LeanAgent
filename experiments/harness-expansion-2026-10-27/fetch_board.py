import json,urllib.request,datetime,subprocess
from pathlib import Path
D=Path(__file__).resolve().parent/'leaderboard';D.mkdir(exist_ok=True)
def get(url,data=None):
 cmd=['curl','--fail','--silent','--show-error','--max-time','90',url]
 if data is not None:cmd+=['-H','Content-Type: application/json','--data',json.dumps(data)]
 return subprocess.check_output(cmd,text=True)
base='https://delta-lab-ai-lean-refactor-arena.hf.space'
r=json.loads(get(base+'/gradio_api/call/leaderboard',{'data':[]}));(D/'request.json').write_text(json.dumps(r))
s=get(base+'/gradio_api/call/leaderboard/'+r['event_id']);(D/'live-response.sse').write_text(s)
for line in s.splitlines():
 if line.startswith('data: '):
  try:
   data=json.loads(line[6:])
   if isinstance(data,list) and data and isinstance(data[0],str): (D/'closed.html').write_text(data[0])
  except json.JSONDecodeError:pass
for name in ['app.py','leaderboard.py','benchmark.py']:
 (D/name).write_text(get('https://huggingface.co/spaces/delta-lab-ai/lean-refactor-arena/raw/main/'+name))
(D/'provenance.json').write_text(json.dumps({'captured_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'url':base,'api':'/gradio_api/call/leaderboard','track':'closed','operation':'read-only public leaderboard'},indent=2))
print('Captured board',len(s),'characters')
