"""Readable full-code export of historical candidate/baseline/final rejections."""
import html,json
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[1];D=H/'failure-code';D.mkdir(exist_ok=True)
E=lambda s:html.escape(str(s))
progress=json.loads((H/'progress.json').read_text())['rows'];by_id={r['id']:r for r in progress};records=[]
for c in map(json.loads,(H/'repair-cases.jsonl').read_text().splitlines()):
 records.append({'id':c['case_id'],'problem_id':c['problem_id'],'name':c['name'],'group':'candidate','label':'후보 검증 거절','code':c['failed_candidate'],'original':c['original'],'feedback':c['feedback'],'context_template':c['context_template']})
for row in progress:
 n=row['id'];raw=R/f'runs/live-practice-2026-10-28/{n}';raw=raw/('raw-v2' if (raw/'raw-v2').exists() else 'raw')
 if row['status'] not in ['baseline_rejected','final_verification_failed']:continue
 problem=json.loads((raw/'input/problem.json').read_text());baseline=row['status']=='baseline_rejected'
 result=json.loads((raw/('baseline/result.json' if baseline else 'final/result.json')).read_text())
 records.append({'id':f'practice-{n}-'+('baseline' if baseline else 'final'),'problem_id':n,'name':row['name'],'group':'baseline' if baseline else 'final','label':'원본 검사 차단' if baseline else '최종 재검증 실패','code':problem['reference'] if baseline else (raw/'selected.lean').read_text(),'original':problem['reference'],'feedback':result,'context_template':str((raw/'input/context.lean.in').relative_to(R))})
parts=['''<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>검증 실패 사례 · 전체 코드</title><style>body{max-width:1120px;margin:auto;padding:28px;background:#f4f7fa;color:#203446;font:17px/1.65 -apple-system,BlinkMacSystemFont,"Apple SD Gothic Neo",sans-serif}section{background:white;padding:20px;border:1px solid #d7e0e6;border-radius:12px;margin:18px 0}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#112a3a;color:#e8f4fc;padding:18px;font:13px/1.6 monospace}summary{cursor:pointer;font-weight:600;padding:10px 0}a{color:#076b98}small{color:#526b7c}</style><h1>검증 실패 기록과 전체 Lean 코드</h1><p>후보 거절 13건 + 원본 검사 차단 12건 + 최종 재검증 실패 1건 = <b>26개 기록</b>. 동일 문제가 여러 번 등장할 수 있다. 모두 과거 실행 기록이며, timeout을 논리적으로 틀린 증명으로 단정하지 않는다. 새 정책은 Lean wall-clock 제한 없음이다.</p><p><b>선언 파일</b>은 theorem/lemma 전체이고, <b>전체 문맥 파일</b>은 당시 context template에 해당 선언을 삽입한 전체 소스다(import·주변 정의 포함). 계측 wrapper는 넣지 않았다. 전체 문맥 파일은 읽기용으로 재구성했으며 이번 내보내기에서 다시 컴파일하지 않았다. 실행하려면 당시 고정된 프로젝트·의존성이 필요하다.</p><p><a href="report.html">전체 리포트</a> · <a href="repair-cases.jsonl">기존 후보 13건 JSONL</a> · <a href="failure-code/index.json">파일 목록 JSON</a></p>''']
index=[]
for group,title in [('candidate','후보 검증 거절 — 모델이 생성한 코드'),('baseline','원본 검사 차단 — 모델 후보 생성 이전'),('final','최종 재검증 실패 — 선택 후 마지막 검사')]:
 parts.append(f'<h2>{title}</h2>')
 for c in records:
  if c['group']!=group:continue
  cid=c['id'];n=c['problem_id'];template=(R/c['context_template']).read_text();assert template.count('{{DECLARATION}}')==1
  full=template.replace('{{DECLARATION}}',c['code']).replace('{{HARNESS_IMPORT}}','').replace('{{HARNESS_COMMANDS}}','')
  (D/(cid+'.declaration.lean')).write_text(c['code']);(D/(cid+'.context.lean')).write_text(full);(D/(cid+'.original.lean')).write_text(c['original'])
  note='과거 거절 기록. 현재 유효성은 해당 후속 검증 기록과 구분해서 확인해야 한다.'
  if n==15 and cid.endswith('002'):note='180초 제한에서 계측 timeout. 동일 코드 사후 재시도 통과, 이후 재선택됨.'
  if n==19:note='180초 제한에서 timeout. 후보2와 최종 선택 코드는 각각 사후 재시도 통과. 후보3은 최종 선택 코드와 동일하다. 원래 실패 기록은 보존.'
  if group=='baseline':note='원본 데이터·입력 검사·공리 검사에서 차단. 실제 sorryAx 의존성과 검사기 오탐을 함께 포함하므로 리포트의 원인 분류를 확인해야 한다.'
  feedback=json.dumps(c['feedback'],ensure_ascii=False,indent=2)
  parts.append(f'<section id="{cid}"><h3>{E(cid)} · {E(c["name"])}</h3><p>{E(note)}</p><p><a href="failure-code/{cid}.declaration.lean">선언 전체 .lean</a> · <a href="failure-code/{cid}.context.lean">import·주변 문맥 포함 전체 .lean</a> · <a href="failure-code/{cid}.original.lean">원본 선언 .lean</a></p><details><summary>거절 당시 코드 전체 펼치기</summary><pre>{E(c["code"])}</pre></details><details><summary>원본 코드 전체 펼치기</summary><pre>{E(c["original"])}</pre></details><details><summary>검증 결과·오류</summary><pre>{E(feedback)}</pre></details></section>')
  index.append({'case_id':cid,'problem_id':n,'name':c['name'],'category':c['label'],'declaration':cid+'.declaration.lean','full_context':cid+'.context.lean','original':cid+'.original.lean','historical_note':note,'source_template':c['context_template'],'recompiled_on_export':False})
(D/'index.json').write_text(json.dumps(index,ensure_ascii=False,indent=2)+'\n');(H/'verification-failures.html').write_text(''.join(parts)+'</html>')
print(f'Exported {len(index)} records; {len({x["problem_id"] for x in index})} unique problems.')
