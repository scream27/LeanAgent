"""Generate the 15-slot dashboard only from a completed revalidation run."""
from pathlib import Path
import argparse
import hashlib
import json

ROOT=Path(__file__).resolve().parents[2]
EXP=Path(__file__).resolve().parent
PRIMARY={'strata':'v4.26.0','physlib':'v4.32.0','cslib':'v4.32.0','arklib':'v4.31.0','putnambench':'v4.26.0'}

def sha(data): return hashlib.sha256(data).hexdigest()
def measurement(result, version):
    e=next(iter(result['environments'].values()))
    return {'tokens':result['tokens'],'heartbeats':e['median_heartbeats']}

def export(runs, output):
    if isinstance(runs, Path): runs=[runs]
    current=(EXP/'manifest.json').read_bytes()
    rows={}; evidence={}; manifest=None; summaries=[]
    for run in runs:
        summary=json.loads((run/'summary.json').read_text())
        if not summary.get('finishedAt'): raise ValueError('Verification is still running')
        if sha(current)!=summary['manifestSha256']: raise ValueError('Import manifest changed after verification')
        imported=json.loads((run/'import-manifest.json').read_text())
        if imported != json.loads(current): raise ValueError('Archived import manifest differs from current input')
        if manifest is not None and imported!=manifest: raise ValueError('Run manifests differ')
        manifest=imported
        if summaries and summary['evaluatorRevision']!=summaries[0]['evaluatorRevision']: raise ValueError('Evaluator versions differ')
        summaries.append(summary)
        for p in summary['problems']:
            rows[p['id']]=p
            evidence[p['id']]=str((run/'summary.json').relative_to(ROOT))
    if set(rows)!=set(range(1,16)): raise ValueError('All fifteen problem records are required')
    summary={**summaries[-1], 'finishedAt':max(s['finishedAt'] for s in summaries)}
    snapshot={'schemaVersion':1,'id':'warmup-team-results','label':'웜업 · 팀원 후보 재검증','dataset':'warmup',
              'measuredAt':summary['finishedAt'],'releaseDate':None,
              'provenance':f"LeanAgent 후보를 PR3 평가기 {summary['evaluatorRevision']}로 재검증. 원본·후보 동일 환경, 3회 중앙값. 기존 보고서 점수 미사용. Track1 API 실행 결과 아님.", 'problems':[]}
    for p in manifest['problems']:
        row=rows[p['id']]; meta=json.loads((EXP/'configs'/f"P{p['id']:02}"/'problem.json').read_text())
        pins=[next(iter(x.items())) for x in meta['version_info']]
        primary=p.get('scoringVersion',PRIMARY[p['source']])
        results=[]
        for c in p['candidates']:
            raw=(ROOT/c['path']).read_bytes()
            if sha(raw)!=c['sha256']: raise ValueError('Candidate changed since verification')
            verified=row['candidates'][c['id']]
            if verified['sha256'] != c['sha256']: raise ValueError('Measured candidate hash differs from imported proof')
            versions=[]; notes=[]
            for version,revision in pins:
                key=f'{version}@{revision}'; result=verified['environments'].get(key)
                status='pending'
                if result is not None:
                    if result['valid']: status='pass'
                    else:
                        errors=[e['error']['kind'] for e in result['environments'].values() if e.get('error')]
                        if any(k in ('compile','axioms') for k in errors): status='fail'
                        notes.append(f'{version}: '+(', '.join(errors) or str(result['error'])))
                elif row['environments'][key].get('reason'):
                    reason=row['environments'][key]['reason']
                    label='원본 검증을 막는 환경/문맥 오류' if '원본 재검증 실패' in reason else ('고정 소스 문맥 미확보' if '소스 없음' in reason else '컴파일러·의존성 준비 필요')
                    notes.append(f'{version}: {label}')
                versions.append({'version':version,'revision':revision,'status':status})
            key=next(f'{v}@{r}' for v,r in pins if v==primary)
            before=row['baseline'].get(key); after=verified['environments'].get(key)
            paired=before and before['valid'] and after and after['valid']
            state='blocked'; baseline=None; candidate=None
            if verified['inputError']:
                state='unsupported';notes.insert(0,'PR3 단일 선언 검증 규약에서 처리하지 못함: '+verified['inputError'])
            elif any(v['status']=='fail' for v in versions): state='proof_failed'
            elif paired:
                state='measured' if all(v['status']=='pass' for v in versions) else 'partial'
                baseline=measurement(before,primary);candidate=measurement(after,primary)
            elif any(v['status']=='pass' for v in versions): state='pending'
            result={'id':c['id'],'author':c['author'],'proof':raw.decode(),'sourcePath':c['sourcePath'],
                    'sourceCommit':c['sourceCommit'],'sourceState':c['sourceState'],'candidateHash':c['sha256'],
                    'status':state,'baseline':baseline,'candidate':candidate,'versions':versions,
                    'environment':f'{primary} · scaled heartbeat · 독립 프로세스 3회 중앙값 · {summary["tokenizer"]}',
                    'note':(' '.join(filter(None,[c['note'],*notes])) or '지정 환경의 원본과 후보를 재검증했습니다.')[:2000]}
            results.append(result)
        selected=next((c for c in results if c['id']==p['representativeId']),None)
        if selected:
            data={k:selected[k] for k in ['status','baseline','candidate','versions','environment','candidateHash','note']}
            base_pass=sum(bool(row['baseline'].get(f'{v}@{r}',{}).get('valid')) for v,r in pins)
            data['baselineCompatibility']=100 if base_pass==len(pins) else None
        else:
            data={'status':'missing','baseline':None,'candidate':None,'versions':[{'version':v,'revision':r,'status':'pending'} for v,r in pins],
                  'environment':'','candidateHash':'','note':'공유된 개선 증명이 없습니다. 기존 원본 fallback은 후보에서 제외했습니다.','baselineCompatibility':None}
        snapshot['problems'].append({'id':p['id'],'name':p['name'],'source':p['source'],**data,
              'evidence':[evidence[p['id']],f"experiments/warmup-team-results/configs/P{p['id']:02}/problem.json"],
              'selectedCandidateId':p['representativeId'] or '', 'selectionReason':p['selectionReason'],'teamResults':results})
    output.mkdir(parents=True,exist_ok=True)
    (output/'warmup-team-results.json').write_text(json.dumps(snapshot,ensure_ascii=False,indent=2)+'\n')
    (output/'index.json').write_text('["warmup-team-results.json"]\n')
    print('Exported 15 problems:',{s:sum(p['status']==s for p in snapshot['problems']) for s in sorted({p['status'] for p in snapshot['problems']})})

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--run',type=Path,required=True,action='append')
    parser.add_argument('--output',type=Path,default=ROOT/'dashboard/public/data')
    args=parser.parse_args();export([p.resolve() for p in args.run],args.output.resolve())
