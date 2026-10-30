"""Deliver a freshly authored response bound to a pending harness request."""
import json,sys,os
from pathlib import Path
HERE=Path(__file__).resolve().parent;REPO=HERE.parents[1]
def reply(n,step,proof,reason,exchange="exchange"):
 d=REPO/'runs/live-practice-2026-10-28'/str(n)/exchange/f'{step:03}';p=json.loads((d/'request.json').read_text())
 if (d/'reply.json').exists():raise FileExistsError('Response already delivered')
 packet={'request_sha256':p['request_sha256'],'content':json.dumps({'proof':proof},ensure_ascii=False),'author':'current conversation model','reason':reason}
 tmp=d/'reply.tmp';tmp.write_text(json.dumps(packet,ensure_ascii=False,indent=2)+'\n');tmp.rename(d/'reply.json')
if __name__=='__main__':reply(int(sys.argv[1]),int(sys.argv[2]),Path(sys.argv[3]).read_text(),sys.argv[4])
