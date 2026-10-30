"""Prepare pinned Strata copy and fixed, conversation-authored proposals; no API."""
import json, shutil, subprocess, hashlib
from pathlib import Path
HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]
WORK=REPO.parent
PROJECT=REPO/'artifacts/repair-bridge/strata'
OLD=WORK/'refactor_arena/strata'
PIN='451e5f047bafa010d178856db76c00029bfa4d7f'
def save(p,x):
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def setup():
 assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=OLD,text=True).strip()==PIN
 if not PROJECT.exists():
  PROJECT.parent.mkdir(parents=True,exist_ok=True)
  shutil.copytree(OLD,PROJECT,ignore=shutil.ignore_patterns('.git','.lake','__pycache__'))
  shutil.copytree(OLD/'.lake',PROJECT/'.lake',symlinks=True)
  for f in subprocess.check_output(['git','ls-files'],cwd=OLD,text=True).splitlines():
   dest=PROJECT/f
   if dest.is_file():
    dest.write_bytes(subprocess.check_output(['git','show','HEAD:'+f],cwd=OLD))
 rows=[json.loads(s) for s in (WORK/'refactor_arena/benchmark_data_warmup.jsonl').read_text().splitlines()][:2]
 source=(PROJECT/rows[0]['file_path']).read_text()
 # These are genuine strategies, not deliberately broken fixtures. Authored once
 # before running Lean; historical work on these two problems was visible.
 bodies=[[
  "by\n  induction post <;> simp_all [substOld, Imperative.HasVarsPure.getVars, Lambda.LExpr.LExpr.getVars, List.Subset]",
  "by\n  induction post <;> unfold substOld <;> (try split <;> try split) <;>\n    simp_all [Imperative.HasVarsPure.getVars, Lambda.LExpr.LExpr.getVars] <;>\n    (repeat' apply List.Subset.app) <;> (try (apply List.Subset.trans; assumption)) <;>\n    simp +contextual [List.Subset, or_imp]",
  rows[0]['src'].split(' := ',1)[1].replace('      have assoc := List.append_assoc (Lambda.LExpr.LExpr.getVars trigger1) (Lambda.LExpr.LExpr.getVars e1) [h1]\n','')
 ],[
  "by\n  intro h\n  induction h <;> simp_all [extractOldExprVars, Imperative.HasVarsPure.getVars, Lambda.LExpr.LExpr.getVars, List.Subset]",
  "by\n  intro h\n  induction h <;> unfold extractOldExprVars <;> (try split) <;>\n    simp_all [Imperative.HasVarsPure.getVars, Lambda.LExpr.LExpr.getVars] <;>\n    (repeat' apply List.Subset.app) <;> (try (apply List.Subset.trans; assumption)) <;>\n    simp +contextual [List.Subset]",
  rows[1]['src'].split(' := ',1)[1].replace('      apply trih <;> assumption','      exact trih tr_normalized')
 ]]
 for i,row in enumerate(rows,1):
  d=HERE/'inputs'/str(i);d.mkdir(parents=True,exist_ok=True)
  assert source.count(row['src'])==1
  template=source.replace(row['src'],'{{DECLARATION}}')
  lines=template.splitlines(True)
  indices=[j for j,l in enumerate(lines) if l.startswith('import ')]
  lines.insert(max(indices)+1,'{{HARNESS_COMMANDS}}\n')
  lines.insert(min(indices),'{{HARNESS_IMPORT}}\n')
  (d/'context.lean.in').write_text(''.join(lines))
  save(d/'problem.json',dict(id=str(i),name=row['name'],statement=row['statement'],reference=row['src'],version_info=row['version_info']))
  save(d/'responses.json',[json.dumps({'proof':b},ensure_ascii=False) for b in bodies[i-1]])
  (d/'prompt.txt').write_text('Refactor only the proof body. Preserve the exact theorem and context. Return JSON with exactly one key, proof. Do not introduce sorry, axioms or target self-reference. Minimize source tokens and elaboration heartbeats.\n')
  # Core harness snapshots this descriptor. PreparedEvaluator explicitly redirects
  # compilation to the separately fingerprinted prepared dependency closure.
  stub=d/'project';stub.mkdir(exist_ok=True)
  (stub/'lean-toolchain').write_text('leanprover/lean4:v4.26.0\n')
  save(d/'config.json',{'schema_version':1,'problem':'problem.json','template':'context.lean.in','project':'project','prompt':'prompt.txt','lean':{'toolchain':'leanprover/lean4:v4.26.0','command':[shutil.which('lake'),'env','lean','-j1'],'timeout_seconds':90,'repetitions':3},'limits':{'max_calls':3,'max_proof_characters':16000,'max_feedback_characters':12000,'max_request_characters':80000},'model':{'backend':'fixture','responses':'responses.json'}})
 save(HERE/'provenance.json',{'upstream_harness_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip(),'strata_commit':PIN,'prepared_project':str(PROJECT),'generation':'This conversation model authored three fixed proposals per problem before verification; historical problem exposure; no independent-model-performance claim','strategies':['induction + broad simplification','structural induction + subset composition (historically informed)','conservative local cleanup'],'api_calls':0,'original_source_sha256':hashlib.sha256(source.encode()).hexdigest()})
if __name__=='__main__': setup()
