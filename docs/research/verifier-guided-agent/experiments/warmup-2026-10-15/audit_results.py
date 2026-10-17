"""Check experiment completeness and selected proof provenance; no Lean or API calls."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main():
    issues = []
    load = lambda p: json.loads(p.read_text())
    manifest = load(HERE / 'manifest.json')
    for name, expected in manifest['hashes'].items():
        if hashlib.sha256((HERE / name).read_bytes()).hexdigest() != expected:
            issues.append(f'Frozen input changed: {name}')
    if hashlib.sha256((HERE/'escalation_policy.py').read_bytes()).hexdigest() != manifest['policy_snapshot_sha256']:
        issues.append('Policy snapshot hash mismatch')
    rows = [json.loads(l) for l in (HERE / 'reference' / 'benchmark_data_warmup.jsonl').read_text().splitlines()]
    selected = load(HERE / 'selected.json')
    count = 0
    for n, row in enumerate(rows, 1):
        choice = next(s for s in selected if s['problem_id'] == n)
        proof_hash = hashlib.sha256(choice['proof_body'].encode()).hexdigest()
        versions = [v for pair in row['version_info'] for v in pair]
        for v in versions:
            path = HERE / 'runs' / f'{n:02d}' / v / 'results.json'
            if not path.exists():
                issues.append(f'{n}/{v}: missing run')
                continue
            run = load(path)
            base = run.get('baseline', {})
            if base.get('kind') != 'valid':
                issues.append(f'{n}/{v}: baseline not verified')
                continue
            count += 1
            obs = [base]
            for c in run.get('candidates', []):
                obs.append(c.get('observation', {}))
                obs.extend(d['observation'] for d in c.get('local', {}).get('derived', []))
            matches = [o for o in obs if o.get('body_hash') == proof_hash]
            if not matches:
                issues.append(f'{n}/{v}: selected body has no observation')
            elif not any(o.get('kind') == 'valid' and set(o.get('axioms') or []) <= set(base.get('axioms') or []) for o in matches):
                issues.append(f'{n}/{v}: selected proof does not pass this version (check reported robustness)')
            if v == versions[0] and base.get('heartbeats') is None:
                issues.append(f'{n}/{v}: baseline heartbeat missing')
    for item in load(HERE / 'results.json'):
        if item['final_outcome'] == 'unresolved':
            issues.append(f"{item['problem_id']}/{item['prompt']}: unresolved")
        if item.get('valid_pool_members_unscored'):
            issues.append(f"{item['problem_id']}/{item['prompt']}: valid pool members not yet scored")
    for path in (HERE / 'policy').glob('*/*/decision.json'):
        decision = load(path)
        if decision.get('api_called') or decision.get('call_authorized'):
            issues.append(f'{path}: unexpected API authorization/call')
    result = {'baseline_version_checks': count, 'expected_baseline_version_checks': sum(len(p) for r in rows for p in r['version_info']),
              'frozen_hashes_checked': len(manifest['hashes']), 'issues': issues, 'complete': not issues}
    (HERE / 'audit.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
