"""Restore frozen PR3 code with one versioned cardinality-filter correction.

Only the bare-# rejection in tokens.py changes. Token counting, comment handling,
Lean execution, heartbeat measurement, and axiom checks stay byte-for-byte frozen.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import subprocess

EVALUATOR_REVISION = 'c18ec56682462847e2f4d8b6d60aa79ec071a10b'
VALIDATOR_VERSION = 'lean-declaration-cardinality-v1'
BASE_VALIDATOR_SHA256 = '733f6ebb4274de88fe448d04879ba3ee58e07e725c62a7e5e4ef122cabf2394d'
VALIDATOR_SHA256 = '514dd5f732ad92ba7c9a8e3dfef45574342e32f15ffda61b9017ca5bd7450cf3'


def evaluator_metadata():
    return {'evaluatorRevision': EVALUATOR_REVISION,
            'validatorVersion': VALIDATOR_VERSION,
            'validatorSha256': VALIDATOR_SHA256}


def patch_validator(source: bytes) -> bytes:
    """Allow adjacent #( and #{; every other # and all other bans still apply."""
    if hashlib.sha256(source).hexdigest() != BASE_VALIDATOR_SHA256:
        raise ValueError('Frozen validator hash mismatch')
    before, after = rb'|#|', rb'|#(?![({])|'
    if source.count(before) != 1:
        raise ValueError('Expected one frozen hash-character filter')
    patched = source.replace(before, after)
    if hashlib.sha256(patched).hexdigest() != VALIDATOR_SHA256:
        raise ValueError('Patched validator hash mismatch')
    return patched


def restore_evaluator(root: Path, runtime: Path):
    names = subprocess.check_output(
        ['git', '-C', str(root), 'ls-tree', '-r', '--name-only',
         EVALUATOR_REVISION, 'refactor_eval'], text=True).splitlines()
    if 'refactor_eval/tokens.py' not in names:
        raise ValueError('Frozen evaluator is missing its validator')
    for name in names:
        source = subprocess.check_output(
            ['git', '-C', str(root), 'show', f'{EVALUATOR_REVISION}:{name}'])
        if name == 'refactor_eval/tokens.py':
            source = patch_validator(source)
        dest = runtime / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(source)
    actual_hash = hashlib.sha256((runtime / 'refactor_eval/tokens.py').read_bytes()).hexdigest()
    if actual_hash != VALIDATOR_SHA256:
        raise ValueError('Restored validator hash mismatch')
    return {**evaluator_metadata(), 'validatorSha256': actual_hash}
