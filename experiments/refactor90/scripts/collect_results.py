"""Collect only hash-matching, compiler-checked candidates; never infer official success."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import sys

import os
if not os.environ.get("ARENA_CORPUS_WORKSPACE"):
    raise RuntimeError("Run this research script through scripts/corpus.py legacy --script refactor90/" + Path(__file__).name)
ROOT = Path(os.environ["ARENA_CORPUS_WORKSPACE"])
sys.path.insert(0, str(ROOT / 'scripts'))
from proof_tokens import proof_length

folder = ROOT / 'refactor90'
selection = json.loads((folder / 'selection.json').read_text())
rows = []
for target in selection['targets']:
    number = target['number']
    home = folder / f'warmup_{number:02}'
    row = dict(target)
    row['official_worker_verified'] = False
    if number == 11:
        path = home / 'candidate-unverified.lean'
        row.update(
            candidate=str(path.relative_to(ROOT)),
            candidate_tokens=proof_length(path.read_text(), (home / 'statement.lean').read_text()),
            compiler_verified=False,
            status='unverified_environment_unavailable',
            note='지정 Lean 버전 및 ArkLib 의존성 미설치. 디스크 여유 약 2.5GiB로 추가 설치 보류. heartbeat 미측정.',
        )
    else:
        suffix = 'listed-local' if number in (6, 7) else '4.26.0'
        checks = {}
        for variant in ('reference', 'best'):
            path = home / f'{variant}.lean'
            check = json.loads((home / f'{variant}.{suffix}.json').read_text())
            assert check['valid'], (number, variant)
            assert check['candidate_sha256'] == hashlib.sha256(path.read_bytes()).hexdigest()
            assert check['tokens'] == proof_length(path.read_text(), (home / 'statement.lean').read_text())
            assert len(check['heartbeats']) == 1
            checks[variant] = check
        baseline, best = checks['reference'], checks['best']
        if number in (13, 14, 15):
            assert baseline['header_sha256'] == best['header_sha256']
        bh = baseline['heartbeats'][0]['raw']
        ch = best['heartbeats'][0]['raw']
        length_ok = best['tokens'] * 10 <= target['reference_length']
        local_hb_ok = ch * 10 <= bh
        published_hb_ok = ch / 1000 * 10 <= target['published_reference_heartbeat']
        row.update(
            candidate=str((home / 'best.lean').relative_to(ROOT)),
            candidate_sha256=best['candidate_sha256'],
            candidate_tokens=best['tokens'],
            length_reduction_pct=100 * (1-best['tokens']/target['reference_length']),
            compiler_verified=True,
            verification_scope=best['scope'],
            lean=best['lean'],
            mathlib=best['mathlib'],
            local_reference_heartbeat_raw=bh,
            local_candidate_heartbeat_raw=ch,
            local_reference_heartbeat=baseline['heartbeats'][0]['scaled'],
            local_candidate_heartbeat=best['heartbeats'][0]['scaled'],
            local_heartbeat_reduction_pct=100*(1-ch/bh),
            published_heartbeat_reduction_pct=100*(1-(ch/1000)/target['published_reference_heartbeat']),
            length_goal_met=length_ok,
            local_heartbeat_goal_met=local_hb_ok,
            published_heartbeat_goal_met=published_hb_ok,
            status='local_both_thresholds_met' if length_ok and local_hb_ok and published_hb_ok else 'partial_improvement_goal_not_met',
            reference_measurement=str((home / f'reference.{suffix}.json').relative_to(ROOT)),
            candidate_measurement=str((home / f'best.{suffix}.json').relative_to(ROOT)),
        )
    rows.append(row)

result = dict(
    generated_at=datetime.now(timezone.utc).isoformat(),
    goal='Each of six problems: at least 90% fewer proof tokens AND at least 90% fewer heartbeats.',
    overall_goal_achieved=False,
    official_submission_performed=False,
    local_both_thresholds_met=sum(r['status']=='local_both_thresholds_met' for r in rows),
    limitations=[
        'Putnam: listed Lean 4.26.0 and pinned Mathlib, but narrowed imports; full Arena header and other listed versions unverified.',
        'CSLib: listed Lean 4.32.0, full source context. PhysLib: listed Lean 4.32.0, unchanged source prefix; later declarations not recompiled.',
        'Heartbeats are local command-elaboration measurements. Published baseline comparisons are reported separately and are not official scores.',
        'Baseline and selected candidate were checked without sorryAx; no theorem statement was changed.',
        'All compiler jobs ran serially with one Lean thread and a 2048 MiB process-group RSS limit.',
    ],
    targets=rows,
)
(folder / 'results.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
for r in rows:
    print(r['number'], r['status'], r.get('candidate_tokens'),
          round(r.get('length_reduction_pct', 0), 2),
          round(r.get('local_heartbeat_reduction_pct', 0), 2))
