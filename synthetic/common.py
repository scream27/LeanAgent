import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import time


def read(path):
    return Path(path).read_bytes().decode('utf-8')


def write(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode('utf-8'))


def save(path, obj):
    write(path, json.dumps(obj, ensure_ascii=False, indent=2) + '\n')


def rows(path):
    return [json.loads(line) for line in read(path).splitlines() if line.strip()]


def jsonl(path, data):
    write(path, ''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in data))


def sha(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def run(command, cwd, timeout=300):
    start = time.perf_counter()
    try:
        p = subprocess.Popen(command, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             start_new_session=os.name != 'nt')
        timed_out = False
        try:
            out, err = p.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            if os.name == 'nt':
                subprocess.run(['taskkill', '/PID', str(p.pid), '/T', '/F'], capture_output=True)
            else:
                os.killpg(p.pid, signal.SIGKILL)
            out, err = p.communicate()
        return dict(command=command, exit_code=p.returncode, stdout=out.decode('utf-8', 'replace'),
                    stderr=err.decode('utf-8', 'replace'), timed_out=timed_out,
                    elapsed_seconds=time.perf_counter() - start)
    except OSError as e:
        return dict(command=command, exit_code=None, stdout='', stderr=str(e), timed_out=False,
                    elapsed_seconds=time.perf_counter() - start)


def git(repo, *args):
    result = run(['git', *args], repo)
    if result['exit_code'] != 0:
        raise RuntimeError(result['stderr'])
    return result['stdout']
