#!/usr/bin/env python3
"""Run one local job with a process-group RSS watchdog and preserved logs."""
import argparse
import json
import os
from pathlib import Path
import signal
import shutil
import subprocess
import time


def group_rss_kb(pgid):
    output = subprocess.check_output(["ps", "-axo", "pgid=,rss="], text=True)
    return sum(int(parts[1]) for line in output.splitlines()
               if len(parts := line.split()) == 2 and int(parts[0]) == pgid)


def run_bounded(command, *, cwd, log, max_rss_mb=1536, timeout=7200, env=None,
                min_free_disk_mb=None):
    log = Path(log)
    log.parent.mkdir(parents=True, exist_ok=True)
    start = time.monotonic()
    peak, reason = 0, None
    child_env = {**os.environ, "LEAN_NUM_THREADS": "1", "ELAN_TOOLCHAIN": "leanprover/lean4:v4.32.0", **(env or {})}
    with log.open("w") as stream:
        process = subprocess.Popen(command, cwd=cwd, env=child_env, stdout=stream,
                                   stderr=subprocess.STDOUT, start_new_session=True)
        while process.poll() is None:
            peak = max(peak, group_rss_kb(process.pid))
            if peak > max_rss_mb * 1024:
                reason = "rss_limit"
            elif (min_free_disk_mb is not None and
                  shutil.disk_usage(cwd).free < min_free_disk_mb * 1024**2):
                reason = "disk_reserve_limit"
            elif time.monotonic() - start > timeout:
                reason = "timeout"
            if reason:
                try:
                    os.killpg(process.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
                time.sleep(0.5)
                if group_rss_kb(process.pid):
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                break
            time.sleep(0.5)
        code = process.wait()
    return {"command": command, "cwd": str(cwd), "returncode": code,
            "stop_reason": reason, "peak_group_rss_mb": round(peak / 1024, 2),
            "max_group_rss_mb": max_rss_mb, "seconds": round(time.monotonic() - start, 3),
            "min_free_disk_mb": min_free_disk_mb,
            "lean_num_threads": 1, "log": str(log)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cwd", type=Path, required=True)
    parser.add_argument("--log", type=Path, required=True)
    parser.add_argument("--max-rss-mb", type=int, default=1536)
    parser.add_argument("--timeout", type=int, default=7200)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command or args.max_rss_mb <= 0:
        parser.error("A command and positive memory limit are required")
    report = run_bounded(command, cwd=args.cwd, log=args.log,
                         max_rss_mb=args.max_rss_mb, timeout=args.timeout)
    args.log.with_suffix(args.log.suffix + ".json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 125 if report["stop_reason"] else report["returncode"]


if __name__ == "__main__":
    raise SystemExit(main())
