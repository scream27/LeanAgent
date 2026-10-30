"""Freeze candidates before Lean results. Conversation-authored proposals, no API."""
import json,hashlib,re,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;REPO=HERE.parents[1];WORK=REPO.parent
ROWS=[json.loads(s) for s in (WORK/'refactor_arena/benchmark_data_warmup.jsonl').read_text().splitlines()]
PIN='c48433678e8fb6306ebcd48453300c8e16058a62'
OLD=WORK/'refactor_arena/prompt_sweep_2026_10_15/environments/physlib'
def write(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def main():
 strategies={}
 for n in (4,5,6):
  row=ROWS[n-1];body=row['src'].split(' := by',1)[1];body='by'+body
  if n==4:
   c1=body.replace('(by simpa [half_pos] using (norm_pos_iff.mpr hx2))','(half_pos (norm_pos_iff.mpr hx2))')
   # Only the final contradiction is rewritten; no statement or premise changes.
   assert c1.endswith('    linarith');c1=c1[:-len('    linarith')]+'    exact (ne_of_gt integral_pos) key_integral'
   c2=body.replace('nlinarith [inner_eq_self_add_diff, hcs, hself, hclose, hxp,\n        mul_lt_mul_of_pos_right hclose hxp]', 'nlinarith [mul_lt_mul_of_pos_right hclose hxp]')
   c3=body.replace('nlinarith [inner_eq_self_add_diff, hcs, hself, hclose, hxp,','nlinarith only [inner_eq_self_add_diff, hcs, hself, hclose, hxp,')
   labels=['direct positivity and contradiction','remove repeated nlinarith hypotheses','restrict nlinarith to explicit premises']
  elif n==5:
   c1=body.replace('(right_eq_inf.mp rfl)','le_top').replace('(ENat.LEInfty.out)','le_top')
   c2=body.replace('simp [Time.deriv_eq]','simp only [Time.deriv_eq]')
   c3=body.replace('rw [Time.deriv_eq]\n      rw [fderiv_fun_sub]','rw [Time.deriv_eq, fderiv_fun_sub]').replace('rw [Time.deriv_eq]\n      rw [fderiv_fun_sum fun i _ => (hBt i).differentiableAt]','rw [Time.deriv_eq, fderiv_fun_sum fun i _ => (hBt i).differentiableAt]').replace('rw [Space.deriv_eq_fderiv_basis]\n        rw [fderiv_fun_sub (hEd _ _).differentiableAt (hEd _ _).differentiableAt]','rw [Space.deriv_eq_fderiv_basis, fderiv_fun_sub (hEd _ _).differentiableAt (hEd _ _).differentiableAt]')
   labels=['canonical le_top proof','narrow derivative simplification','batch adjacent rewrites']
  else:
   c1=body.replace('repeat rw [mul_assoc]','simp only [mul_assoc]').replace('repeat rw [ofCrAnListF_append]','simp only [ofCrAnListF_append]')
   # Predicate proofs do not use the span-membership proof parameter.
   c2=re.sub(r' \(hc : [ab] ∈ Submodule\.span ℂ \(Set\.range ofCrAnListFBasis\)\)', '',body)
   c2=c2.replace('change pb b (Basis.mem_span _ b)','change pb b').replace('change pa a (Basis.mem_span _ a)','change pa a')
   c3=body.replace('simp_all [pa,mul_add, add_mul]','simp only [pa, mul_add, add_mul, map_add, map_mul, hpx, hpy]').replace('simp_all [pb,mul_add]','simp only [pb, mul_add, map_add, hpx, hpy]')
   labels=['replace repeated rewrite traversal','remove unused dependent predicate arguments','narrow linearity simplification']
  candidates=[c1,c2,c3];assert len(set(candidates))==3 and all(c!=body for c in candidates)
  source=subprocess.check_output(['git','show',PIN+':'+row['file_path']],cwd=OLD,text=True)
  assert source.count(row['src'])==1
  template=source.replace(row['src'],'{{DECLARATION}}')
  lines=template.splitlines(True);imports=[i for i,l in enumerate(lines) if re.match(r'^(public )?import ',l)]
  lines.insert(max(imports)+1,'{{HARNESS_COMMANDS}}\n');lines.insert(min(imports),'{{HARNESS_IMPORT}}\n')
  d=HERE/'inputs'/str(n);d.mkdir(parents=True,exist_ok=True)
  (d/'context.lean.in').write_text(''.join(lines));write(d/'problem.json',{'id':str(n),'name':row['name'],'statement':row['statement'],'reference':row['src'],'version_info':row['version_info']})
  write(d/'responses.json',[json.dumps({'proof':c},ensure_ascii=False) for c in candidates]);write(d/'strategies.json',labels)
  (d/'prompt.txt').write_text('Refactor only the existing proof body. Preserve all statements and surrounding definitions. Return JSON with exactly one proof field. Prefer verified simplification and lower elaboration cost; no sorry, new axioms or target self-reference.\n')
  stub=d/'project';stub.mkdir(exist_ok=True);(stub/'lean-toolchain').write_text('leanprover/lean4:v4.32.0\n')
  write(d/'config.json',{'schema_version':1,'problem':'problem.json','template':'context.lean.in','project':'project','prompt':'prompt.txt','lean':{'toolchain':'leanprover/lean4:v4.32.0','command':[sys.executable,str(HERE/'lean_command.py'),'-j1'],'timeout_seconds':180,'repetitions':3},'limits':{'max_calls':3,'max_proof_characters':40000,'max_feedback_characters':12000,'max_request_characters':150000},'model':{'backend':'fixture','responses':'responses.json'}})
  strategies[n]=labels
 write(HERE/'candidate-freeze.json',{'harness_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip(),'problem_ids':[4,5,6],'generation':'conversation-authored fixed candidates; no live-model performance claim, no deliberately broken mutation','api_calls':0,'strategies':strategies,'sha256':{str(p.relative_to(HERE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (HERE/'inputs').rglob('*') if p.is_file()}})
if __name__=='__main__':main()
