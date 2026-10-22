"""Export read-only, provenance-linked snapshots; never runs Lean or rewrites evidence."""
import argparse
import json
import statistics
from pathlib import Path

DASHBOARD = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads(path.read_text())


def empty_problem(number, status="unreleased"):
    return dict(id=number, name="", source="unknown", status=status, baseline=None,
                candidate=None, baselineCompatibility=None, versions=[], environment="",
                candidateHash="", evidence=[], note="2026년 11월 1일 공개 예정 · 공개 후 데이터 연결")


def historical(root):
    path = root / "research/arena-all-sol-high-2026-10-09/summary.json"
    rows = []
    for row in read(path)["problems"]:
        valid = {v: x for v, x in row["versions"].items() if x.get("comparison_eligible")}
        version = next((v for v in ("v4.26.0", "v4.32.0", "v4.31.0", "v4.29.0") if v in valid), next(iter(valid)))
        metrics = valid[version]
        checks = []
        original_passes = 0
        for pin in row["required_versions"]:
            for v, revision in pin.items():
                result = row["versions"].get(v, {})
                same_pin = result.get("commit") == revision
                state = "pending"
                if same_pin and result.get("comparison_eligible"):
                    state = "pass" if result.get("selected_valid") else "fail"
                checks.append(dict(version=v, revision=revision, status=state))
                original_passes += bool(same_pin and result.get("original_valid"))
        rows.append(dict(id=int(row["problem"][:2]), name=row["name"], source=row["problem"].split("-", 1)[1],
                         status="measured", baseline=dict(tokens=row["original_tokens"], heartbeats=metrics["original_heartbeat"]),
                         candidate=dict(tokens=row["selected_token_counts"]["statement_anchored"], heartbeats=metrics["selected_heartbeat"]),
                         baselineCompatibility=100 if original_passes == len(checks) else None,
                         versions=checks, environment=f"Lean {version.removeprefix('v')} · {metrics['commit'][:10]} · scaled heartbeat",
                         candidateHash=row["candidate_sha256"], evidence=[str(path.relative_to(root)), row["candidate"]],
                         note=row["insight"] + " 대표 버전 하나의 동일 환경 측정값입니다. 공식 worker 평가는 아닙니다."))
    return dict(schemaVersion=1, id="warmup-2026-10-10", label="10.10 · 전체 버전 검증", dataset="warmup",
                measuredAt="2026-10-10T00:00:00+09:00", releaseDate=None,
                provenance="LEArN/research/arena-all-sol-high-2026-10-09/summary.json · 완료일 기준, 시각 미기록", problems=rows)


def latest(root):
    folder = root / "week3-experiments/experiments/evidence/2026-10-16-warmup15-xhigh"
    invalidations = read(folder / "audit-invalidations.json")
    rows, timestamps = [], []
    for number in range(1, 16):
        directory = folder / f"P{number:02}"
        selection = read(directory / "best.json")
        meta = read(directory / "metadata.json")
        base, best = selection.get("baseline"), selection.get("best")
        row = empty_problem(number, "pending")
        row.update(name=meta["name"], source=meta["source"], note="이번 실험의 전체 문맥 측정 대기. 이전 결과는 ‘10.10 · 전체 버전 검증’에서 확인할 수 있습니다.")
        checks = [dict(version=v, revision=rev, status="pending") for pin in meta["version_info"] for v, rev in pin.items()]
        row["versions"] = checks
        if base and base.get("valid") and best and len(best.get("runs", [])) >= 2:
            evidence_paths, verified_runs = [], []
            for old_path in best["runs"]:
                if old_path in invalidations:
                    raise ValueError(f"Invalidated selected measurement: P{number}")
                # Historic evidence was recorded on another machine; only remap the known Pxx suffix.
                suffix = old_path.split(f"/P{number:02}/", 1)[1]
                local = (directory / suffix).resolve()
                if not local.is_relative_to(directory.resolve()):
                    raise ValueError("Evidence path escaped problem directory")
                run = read(local)
                if not run.get("valid") or run.get("proof_sha256") != best["proof_sha256"]:
                    raise ValueError(f"Selected candidate verification mismatch: P{number}")
                if run.get("environment", {}).get("lean_version") != base["environment"]["lean_version"] or run.get("environment", {}).get("source_revision") != base["environment"]["source_revision"]:
                    raise ValueError(f"Measurement environment mismatch: P{number}")
                evidence_paths.append(str(local.relative_to(root)))
                verified_runs.append(run)
                timestamps.append(run["finished_at"])
            if base.get("result_path") in invalidations:
                raise ValueError(f"Invalidated baseline: P{number}")
            actual = statistics.median(r["raw_heartbeats"] for r in verified_runs)
            if actual != best["raw_heartbeats_median"] or any(r["proof_tokens"] != best["proof_tokens"] for r in verified_runs):
                raise ValueError(f"Selected measurement disagrees with evidence: P{number}")
            env = base["environment"]
            for check in checks:
                if check["version"].removeprefix("v") == env["lean_version"] and check["revision"] == env["source_revision"]:
                    check["status"] = "pass"
            row.update(status="measured", baseline=dict(tokens=base["proof_tokens"], heartbeats=base["raw_heartbeats"]),
                       candidate=dict(tokens=best["proof_tokens"], heartbeats=actual),
                       baselineCompatibility=100 if len(checks) == 1 and checks[0]["status"] == "pass" else None,
                       environment=f"Lean {env['lean_version']} · {env['source_revision'][:10]} · raw heartbeat",
                       candidateHash=best["proof_sha256"], evidence=[str((directory / "best.json").relative_to(root))] + evidence_paths,
                       note="전체 문맥에서 동일 후보를 2회 이상 검증했습니다. Heartbeat는 raw 중앙값이며 원본도 같은 단위입니다. 다른 버전의 미확인 결과를 성공으로 간주하지 않습니다.")
        rows.append(row)
    return dict(schemaVersion=1, id="warmup-2026-10-16", label="10.16 · 추가 개선 실험", dataset="warmup", measuredAt=max(timestamps),
                releaseDate=None, provenance=str(folder.relative_to(root)) + "/Pxx/best.json · 로컬 실험", problems=rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--learn-root", type=Path, default=DASHBOARD.parent.parent / "LEArN")
    args = parser.parse_args()
    root = args.learn_root.resolve()
    output = DASHBOARD / "public/data"
    output.mkdir(parents=True, exist_ok=True)
    snapshots = [latest(root), historical(root)]
    for snapshot in snapshots:
        snapshot["dataset"] = "competition"
        snapshot["releaseDate"] = "2026-11-01"
        snapshot["provenance"] += " · 현재 15문제를 포함한 50문제 구성, 번호는 내부 관리용"
        snapshot["problems"].extend(empty_problem(i) for i in range(16, 51))
    for snapshot in snapshots:
        target = output / (snapshot["id"] + ".json")
        target.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n")
    (output / "index.json").write_text(json.dumps([s["id"] + ".json" for s in snapshots], indent=2) + "\n")
    print(f"Exported {len(snapshots)} snapshots of 50 slots: 15 existing + 35 unreleased. No proof source or machine-specific paths exported.")


if __name__ == "__main__":
    main()
