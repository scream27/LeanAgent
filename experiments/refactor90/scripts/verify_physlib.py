"""Warmup 06: original imports and declarations before the target, pinned 4.32.0."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import os
if not os.environ.get("ARENA_CORPUS_WORKSPACE"):
    raise RuntimeError("Run this research script through scripts/corpus.py legacy --script refactor90/" + Path(__file__).name)
ROOT = Path(os.environ["ARENA_CORPUS_WORKSPACE"])
sys.path.insert(0, str(ROOT / 'scripts'))
from run_physlib_bounded import run_bounded
from proof_tokens import proof_length
from verify_dev import WRAPPER
ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument('--variant', default='candidate')
args = ap.parse_args()
folder = ROOT / 'refactor90/warmup_06'
cache = Path(os.environ['PROJECT_CACHE_DIR']) / 'refactor90/cslib-4.32.0'
source = (ROOT / 'sources/physlib/Physlib/QFT/PerturbationTheory/WickAlgebra/TimeOrder.lean').read_text()
reference = (folder / 'reference.lean').read_text().strip()
assert source.count(reference) == 1
before, after = source.split(reference)
declaration = (folder / f'{args.variant}.lean').read_text()
target = cache / f'Warmup06-{args.variant}.lean'
target.write_text(before + '\n' + WRAPPER + '\n#measure_refactor\n' + declaration +
                  '\nend WickAlgebra\nend FieldSpecification\n' +
                  '#print axioms FieldSpecification.WickAlgebra.ι_timeOrderF_superCommuteF_eq_time\n')
plan = json.loads((ROOT / 'refactor90/physlib-build-plan.json').read_text())
env = {'LEAN_PATH': ':'.join([str(cache)] + plan['lean_path']), 'ELAN_TOOLCHAIN': 'leanprover/lean4:v4.32.0'}
result = run_bounded(['/Users/jwkweon/.elan/toolchains/leanprover--lean4---v4.32.0/bin/lean', str(target)],
                     cwd=cache, log=cache / f'Warmup06-{args.variant}.log',
                     max_rss_mb=2048, timeout=180, env=env)
log = Path(result['log']).read_text()
matches = re.findall(r'MEASURE_HEARTBEATS raw=(\d+) scaled=(\d+)', log)
result.update(scope='listed_environment_local_original_predeclaration_context', lean='4.32.0',
              physlib='c48433678e8fb6306ebcd48453300c8e16058a62',
              mathlib='81a5d257c8e410db227a6665ed08f64fea08e997',
              tokens=proof_length(declaration, (folder / 'statement.lean').read_text()),
              candidate_sha256=hashlib.sha256(declaration.encode()).hexdigest(),
              valid=result['returncode'] == 0 and 'sorryAx' not in log and len(matches) == 1,
              heartbeats=[{'raw': int(a), 'scaled': int(b)} for a,b in matches])
(folder / f'{args.variant}.listed-local.json').write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps(result, indent=2))
print(log[:2500] + ('\n[truncated; see log file]\n'+log[-2500:] if len(log)>2500 else ''))
