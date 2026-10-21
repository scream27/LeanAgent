"""Build the pinned cache client, then fetch only selected proof dependencies.

Uses upstream cache hashing/download/decompression APIs unchanged. ProofWidgets
web assets are unnecessary for command-line checking and are not fetched.
"""
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
from proof_tokens import remove_comments
from run_physlib_bounded import run_bounded
root = Path(os.environ['PROJECT_CACHE_DIR']) / 'refactor90/mathlib-4.26.0'
lean = '/Users/jwkweon/.elan/toolchains/leanprover--lean4---v4.26.0/bin/lean'
roots = [root] + list((root / '.lake/packages').iterdir())
libs = [p / '.lake/build/lib/lean' for p in roots]
env = {'LEAN_PATH': ':'.join(map(str, libs)), 'LEAN_SRC_PATH': ':'.join(map(str, roots)),
       'ELAN_TOOLCHAIN': 'leanprover/lean4:v4.26.0', 'RAYON_NUM_THREADS': '1',
       'MATHLIB_CACHE_DIR': '/Users/jwkweon/00_work/00_project/cache/_shared/mathlib'}
seen = set()
def build(module):
    if module in seen:
        return
    seen.add(module)
    rel = Path(module.replace('.', '/') + '.lean')
    home = next((p for p in roots if (p / rel).exists()), None)
    if home is None:
        return  # Lean/Std provided by the installed toolchain.
    target = home / '.lake/build/lib/lean' / rel.with_suffix('.olean')
    if target.exists():
        return
    for line in remove_comments((home / rel).read_text()).splitlines():
        match = re.match(r'\s*(?:public |meta )*import\s+(?:all\s+)?(.*)', line)
        if match:
            for dep in match[1].split():
                build(dep)
    target.parent.mkdir(parents=True, exist_ok=True)
    result = run_bounded([lean, '-Dexperimental.module=true', '--root='+str(home), '-o', str(target), str(home / rel)],
                         cwd=home, log=root / 'logs' / (module+'.log'),
                         max_rss_mb=1536, timeout=120, env=env)
    print(module, result['returncode'], flush=True)
    if result['returncode']:
        print(Path(result['log']).read_text()[-3000:])
        raise SystemExit(1)
build('Cache.Requests')
helper = root / 'FetchSelected.lean'
helper.write_text('''import Cache.Requests
open Cache IO Hashing Requests in
def main (args : List String) : IO Unit := CacheM.run do
  let roots ← parseArgs ("get" :: args)
  let memo ← getHashMemo roots
  let hashes ← memo.filterByRootModules roots.keys
  IO.println s!"Selected dependency closure: {hashes.size} modules"
  validateLeanTar
  downloadFiles "leanprover-community/mathlib4" hashes false true (warnOnMissing := true)
  unpackCache hashes false
''')
modules = ['Mathlib.Combinatorics.SetFamily.Intersecting', 'Mathlib.Data.Fintype.Powerset',
           'Mathlib.Data.Fintype.BigOperators', 'Mathlib.Data.Int.Interval',
           'Mathlib.Data.Real.Basic', 'Mathlib.Data.Fintype.Pi',
           'Mathlib.Order.Preorder.Finite', 'Mathlib.Data.Fintype.Pigeonhole',
           'Mathlib.Tactic.Push', 'Mathlib.Tactic.Tauto', 'Mathlib.Tactic.NormNum',
           'Mathlib.Tactic.Linarith', 'Mathlib.Tactic.Ring', 'Mathlib.Tactic.FieldSimp',
           'Mathlib.RingTheory.Coprime.Lemmas', 'Mathlib.Algebra.BigOperators.Ring.Finset',
           'Mathlib.Data.Nat.Prime.Basic', 'Mathlib.RingTheory.Int.Basic', 'Aesop']
result = run_bounded([lean, '-Dexperimental.module=true', '--run', str(helper), *modules], cwd=root,
                     log=root / 'logs/fetch.log', max_rss_mb=2048, timeout=600, env=env,
                     min_free_disk_mb=2048)
(root / 'fetch-result.json').write_text(json.dumps(result, indent=2))
print(json.dumps(result, indent=2))
print(Path(result['log']).read_text()[-4000:])
