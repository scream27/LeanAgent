"""Import audited helpers from a pinned checkout; do not vendor unlicensed code."""
import importlib
from pathlib import Path
import sys
from .common import git

AURASOPH_COMMIT = '7f3a401470d04f70013d293db4253b088ec8a0ae'
DELTA_COMMIT = 'a2372caad69ab61a42a0e997106b87e00d9d7d65'


def helpers(root):
    root = Path(root).resolve()
    if git(root, 'rev-parse', 'HEAD').strip() != AURASOPH_COMMIT:
        raise ValueError('Upstream checkout must match audited commit')
    if git(root, 'status', '--porcelain', '--untracked-files=no').strip():
        raise ValueError('Upstream helper code has tracked modifications')
    sys.path.insert(0, str(root / 'competition'))
    sys.path.insert(0, str(root / 'mining'))
    return importlib.import_module('find_problems'), importlib.import_module('local_score')
