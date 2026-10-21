"""Sequential, memory-bounded build of the selected CSLib dependency closure."""
import json
import os
from pathlib import Path
import sys
import argparse
import shutil
import os
if not os.environ.get("ARENA_CORPUS_WORKSPACE"):
    raise RuntimeError("Run this research script through scripts/corpus.py legacy --script refactor90/" + Path(__file__).name)
ROOT = Path(os.environ["ARENA_CORPUS_WORKSPACE"])
sys.path.insert(0, str(ROOT / 'scripts'))
from run_physlib_bounded import run_bounded
ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument('--plan', default='cslib-build-plan.json')
args = ap.parse_args()
plan = json.loads((ROOT / 'refactor90' / args.plan).read_text())
cache = Path(os.environ['PROJECT_CACHE_DIR']) / 'refactor90/cslib-4.32.0'
cache.mkdir(parents=True, exist_ok=True)
env = {'LEAN_PATH': ':'.join([str(cache)] + plan['lean_path']),
       'ELAN_TOOLCHAIN': 'leanprover/lean4:v4.32.0'}
reports = []
for module, source in plan['plan']:
    target = cache / (module.replace('.', '/') + '.olean')
    if target.exists():
        continue
    if shutil.disk_usage(cache).free < 2 * 1024**3:
        print('Stopped: less than 2 GiB free disk space', flush=True)
        break
    target.parent.mkdir(parents=True, exist_ok=True)
    root = str(Path(source).parents[len(module.split('.'))-1])
    cmd = ['/Users/jwkweon/.elan/toolchains/leanprover--lean4---v4.32.0/bin/lean',
           '--root=' + root, '-o', str(target), source]
    result = run_bounded(cmd, cwd=root, log=cache / 'logs' / (module + '.log'),
                         max_rss_mb=2048, timeout=180, env=env)
    reports.append(result)
    (cache / (args.plan + '.results.json')).write_text(json.dumps(reports, indent=2))
    print(module, result['returncode'], result['seconds'], result['peak_group_rss_mb'], flush=True)
    if result['returncode']:
        print(Path(result['log']).read_text()[-5000:])
        break
