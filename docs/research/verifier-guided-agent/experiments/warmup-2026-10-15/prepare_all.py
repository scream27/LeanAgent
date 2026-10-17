"""Sequential, pinned environment setup and execution. Network access required.

Only this experiment's .lake build/download directories are reclaimed between
environments. User projects and existing toolchains are never deleted.
"""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
ROWS = [json.loads(l) for l in (HERE/'reference/benchmark_data_warmup.jsonl').read_text().splitlines()]
ENVS = HERE/'environments'
ELAN = str(Path.home()/'.elan/bin/elan')
LAKE = str(Path.home()/'.elan/bin/lake')
PYTHON = str(HERE/'.venv/bin/python')


def call(cmd, cwd, env, logfile, timeout=3600):
    print('RUN', ' '.join(cmd), flush=True)
    with logfile.open('w') as f:
        try:
            p = subprocess.run(cmd, cwd=cwd, env=env, stdout=f, stderr=subprocess.STDOUT, timeout=timeout)
            rc = p.returncode
        except subprocess.TimeoutExpired:
            rc = 124
    print('EXIT', rc, logfile.name, flush=True)
    return rc


def main():
    jobs = {}
    for n, r in enumerate(ROWS, 1):
        for pair in r['version_info']:
            for v, commit in pair.items():
                jobs.setdefault((r['source'], v, commit), []).append(n)
    # Existing Strata 4.26 is handled separately. Physlib is currently being prepared.
    for (source, v, commit), ids in jobs.items():
        only=[a[len('--only='):] for a in sys.argv if a.startswith('--only=')]
        if only and source+':'+v not in only:
            continue
        if source == 'strata' and v == 'v4.26.0':
            continue
        if source == 'physlib' and '--skip-physlib' in sys.argv:
            continue
        logdir = HERE/'setup_logs'/f'{source}_{v}'
        logdir.mkdir(parents=True, exist_ok=True)
        env = dict(os.environ)
        if v != 'v4.26.0':
            env['ELAN_HOME'] = str(ENVS/'elan')
        # Redirect caches into the disposable experiment space.
        env['XDG_CACHE_HOME'] = str(ENVS/'download_cache')
        project = ENVS/source
        url = ROWS[ids[0]-1]['url'] or 'https://github.com/leanprover-community/mathlib4.git'
        status = {'source': source, 'version': v, 'commit': commit, 'ids': ids, 'stage': 'setup'}
        def record():
            (logdir/'status.json').write_text(json.dumps(status, indent=2))
        record()
        steps = []
        if not project.exists():
            steps.append((['git','clone','--depth','1',url,str(project)], HERE))
        for k, (cmd, cwd) in enumerate(steps):
            if call(cmd, cwd, env, logdir/f'clone{k}.log'):
                status['stage'] = 'clone_failed'; break
        if status['stage'] != 'setup': record(); continue
        if call(['git','fetch','--depth','1','origin',commit],project,env,logdir/'fetch.log'):
            status['stage']='fetch_failed';record();continue
        if call(['git','checkout','--detach',commit],project,env,logdir/'checkout.log'):
            status['stage']='checkout_failed';record();continue
        if v != 'v4.26.0' and call([ELAN,'toolchain','install','leanprover/lean4:'+v],project,env,logdir/'toolchain.log'):
            status['stage']='toolchain_failed';record();continue
        expected=(project/'lean-toolchain').read_text().strip()
        if expected != 'leanprover/lean4:'+v:
            status.update(stage='toolchain_mismatch',actual=expected);record();continue
        # Mathlib-based projects have a downloadable cache; Strata builds directly.
        if source != 'strata':
            status['cache_rc']=call([LAKE,'exe','cache','get'],project,env,logdir/'cache.log')
            if status['cache_rc']:
                status['stage']='cache_failed';record();continue
        if source != 'putnambench':
            targets = sorted({ROWS[n-1]['file_path'][:-5].replace('/','.') for n in ids})
            rc=call([LAKE,'build',*targets],project,env,logdir/'build.log')
            if rc:
                status['stage']='build_failed';record();continue
        status['stage']='verifying';record()
        status['run_rc']=call([PYTHON,'-B',str(HERE/'run_sweep.py'),source,v,str(project),*map(str,ids)],HERE,env,logdir/'run.log')
        status['stage']='finished';record()
        # The result files contain source snapshots and logs; build artifacts are expendable.
        lake=project/'.lake'
        if lake.exists():
            shutil.rmtree(lake)
        cache=ENVS/'download_cache'
        if cache.exists():
            shutil.rmtree(cache)
        # Reclaim only toolchains installed in this experiment, after their job.
        tc=ENVS/'elan/toolchains'/('leanprover--lean4---'+v)
        if tc.exists():
            shutil.rmtree(tc)
        print('FINISHED',source,v,'free GiB',round(shutil.disk_usage(HERE).free/2**30,1),flush=True)


if __name__ == '__main__': main()
