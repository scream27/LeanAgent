"""Bounded Putnam check with narrowed imports; not an official Arena worker run."""
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

PACKAGES = Path('/Users/jwkweon/00_work/00_project/cache/05_pseudolab/ai4math/lean/.lake/packages')
LEAN = '/Users/jwkweon/.elan/toolchains/leanprover--lean4---v4.33.1/bin/lean'
WRAPPER = '''
set_option Elab.async false
set_option maxHeartbeats 200000
open Lean Elab Command in
elab "#measure_refactor " cmd:command : command => do
  let start ← IO.getNumHeartbeats
  elabCommand cmd
  let finish ← IO.getNumHeartbeats
  logInfo m!"MEASURE_HEARTBEATS raw={finish - start} scaled={(finish - start) / 1000}"
'''

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('number', type=int)
    ap.add_argument('--variant', default='candidate')
    ap.add_argument('--lean-version', choices=['4.33.1', '4.26.0'], default='4.33.1')
    args = ap.parse_args()
    folder = ROOT / 'refactor90' / f'warmup_{args.number:02}'
    declaration = (folder / f'{args.variant}.lean').read_text()
    statement = (folder / 'statement.lean').read_text()
    meta = json.loads((folder / 'metadata.json').read_text())
    name = meta['name']
    cache = Path(os.environ['PROJECT_CACHE_DIR']) / 'refactor90' / f'warmup_{args.number:02}' / args.lean_version
    cache.mkdir(parents=True, exist_ok=True)
    src = cache / f'{args.variant}.lean'
    header_path = folder / 'development-header.lean'
    header = (header_path if header_path.exists() else folder / 'header.lean').read_text()
    diagnostic = '''
open Lean Elab Tactic in
elab "traceHB" : tactic => do
  logInfo m!"TRACE_HB {← IO.getNumHeartbeats}"
''' if args.variant.startswith('profile') else ''
    src.write_text(header + '\n' + WRAPPER + diagnostic + '\n#measure_refactor\n' + declaration + '\n#print axioms ' + name + '\n')
    packages = PACKAGES
    roots = []
    if args.lean_version == '4.26.0':
        pinned = Path(os.environ['PROJECT_CACHE_DIR']) / 'refactor90/mathlib-4.26.0'
        packages = pinned / '.lake/packages'
        roots.append(pinned)
    roots.extend(p for p in packages.iterdir() if p.is_dir())
    lean_path = ':'.join(str(p / '.lake/build/lib/lean') for p in roots)
    lean = LEAN.replace('v4.33.1', 'v'+args.lean_version)
    result = run_bounded([lean, str(src)], cwd=cache, log=cache / f'{args.variant}.log',
                         max_rss_mb=2048, timeout=120,
                         env={'LEAN_PATH': lean_path, 'ELAN_TOOLCHAIN': 'leanprover/lean4:v'+args.lean_version})
    log = Path(result['log']).read_text()
    matches = re.findall(r'MEASURE_HEARTBEATS raw=(\d+) scaled=(\d+)', log)
    result.update(scope='listed_version_narrow_imports' if args.lean_version == '4.26.0' else 'development_only_not_listed_environment', lean=args.lean_version,
                  mathlib='2df2f0150c275ad53cb3c90f7c98ec15a56a1a67' if args.lean_version == '4.26.0' else '0df444a360eaa60ab8c11dca51a86af692955474',
                  header_path=str(header_path),
                  header_sha256=hashlib.sha256(header.encode()).hexdigest(),
                  tokens=proof_length(declaration, statement),
                  candidate_sha256=hashlib.sha256(declaration.encode()).hexdigest(),
                  valid=result['returncode'] == 0 and 'sorryAx' not in log and len(matches) == 1,
                  heartbeats=[{'raw': int(a), 'scaled': int(b)} for a,b in matches])
    (folder / f'{args.variant}.{args.lean_version}.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))
    print(log[:2500] + ('\n[truncated; see log file]\n' + log[-1500:] if len(log) > 4000 else log[2500:]))

if __name__ == '__main__':
    main()
