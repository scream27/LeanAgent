"""Independent integrity checks on the final experiment artifacts."""
import json,hashlib,subprocess
from pathlib import Path
from run import HERE,REPO,PROJECT

def main():
 data=json.loads((HERE/'results.json').read_text());exports=json.loads((HERE/'arena-submission.json').read_text());checks=[]
 for path,digest in json.loads((HERE/'candidate-freeze.json').read_text())['sha256'].items():
  assert hashlib.sha256((HERE/path).read_bytes()).hexdigest()==digest,path
 checks.append('All frozen input hashes match')
 assert len(exports)==3
 for row,out in zip(data['problems'],exports):
  n=row['id'];problem=json.loads((HERE/'inputs'/str(n)/'problem.json').read_text());raw=REPO/row['raw_run']
  assert out['name']==problem['name'] and out['proof']==(raw/'selected.lean').read_text()
  assert out['proof'].startswith(problem['statement']+' :=')
  assert row['final_valid'] and row['replay']['record_replay_passed']
  assert row['selected']['rank_numerator']<=2*row['baseline']['tokens']*row['baseline']['raw_heartbeats']
  for stage in ['baseline','final']:
   r=json.loads((raw/stage/'result.json').read_text());assert r['valid']
   runs=r['environments']['fixed']['runs'];assert len(runs)==4
   assert all(x['returncode']==0 and not x['timed_out'] for x in runs)
   assert all(set(x['measurement']['axioms'])<={'propext','Classical.choice','Quot.sound'} for x in runs if 'measurement' in x)
  checks.append(f'P{n}: fixed statement, valid final, no worse selection, 3 fresh samples, replay, safe axioms')
 assert not subprocess.check_output(['git','diff','HEAD','--','.'],cwd=PROJECT).strip()
 checks.append('Prepared upstream source remains unchanged')
 (HERE/'audit.json').write_text(json.dumps({'passed':True,'checks':checks},indent=2)+'\n')
 print('\n'.join(checks))
if __name__=='__main__':main()
