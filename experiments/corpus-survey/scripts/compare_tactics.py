#!/usr/bin/env python3
"""Stream two pinned proof inventories through the same lexical tactic counter.

No Lean, network, build, or heartbeat operation is performed. The baseline is
survey.tactic_heads, so results can be compared with the earlier pilot survey.
"""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
from itertools import combinations
import json
from pathlib import Path
import re

from survey import TACTICS, COMBINATORS, TOKEN, mask_noncode, tactic_heads

from arena_workspace import ROOT
AMBIGUOUS = {"have", "show", "calc", "suffices", "congrArg", "rfl", "refl", "funext", "decide", "let", "letI", "haveI", "replace", "set"}
BRANCH = {"case", "next"}
CONV = {"conv", "conv_lhs", "conv_rhs", "enter"}
WRAPPERS = {"with_unfolding_all", "solve"}
EXTENSIONS = set("""fun_prop conv_lhs fin_cases erw refine' conv_rhs filter_upwards
convert! set ext1 linear_combination replace conv abel with_unfolding_all
nth_rewrite nth_rw module contrapose! push_cast measurability noncomm_ring
continuity ring_nf! done subst_vars decreasing_tactic enter trans symm
generalize_proofs grw swap choose apply_rules rotate_left matrix_expand
split_contra_case false_or_by_contra solve_beq expose_names split_contra
fun_induction solve let letI haveI""".split())


def simp_only_after(masked: str, start: int) -> bool:
    """Recognize only after simp's optional parenthesized config and +/- flags."""
    pos = start
    while pos < len(masked):
        while pos < len(masked) and masked[pos].isspace():
            pos += 1
        if re.match(r"only\b", masked[pos:]):
            return True
        flag = re.match(r"[+-][\w.]+", masked[pos:])
        if flag:
            pos += len(flag[0])
        elif pos < len(masked) and masked[pos] == "(":
            depth = 1
            pos += 1
            while pos < len(masked) and depth:
                if masked[pos] == "(":
                    depth += 1
                elif masked[pos] == ")":
                    depth -= 1
                pos += 1
            if depth:
                return False
        else:
            return False
    return False


def extended_heads(source: str) -> list[dict]:
    """Same boundary heuristic, expanded allowlist and projection correction.

    Token/offset behavior deliberately matches survey.tactic_heads. A contiguous
    `.head` is a projection/qualified identifier, not a tactic bullet.
    """
    masked = mask_noncode(source)
    hits = []
    previous, last_end, line, last_pos = None, 0, 1, 0
    for match in TOKEN.finditer(masked):
        word = match[0]
        gap = masked[last_end:match.start()]
        line += masked[last_pos:match.start()].count("\n")
        boundary = previous is None or "\n" in gap or previous in {"by", ";", "<;>", "=>", "|", "·", "(", *COMBINATORS, *WRAPPERS} or (previous == "." and bool(gap))
        if boundary and word in TACTICS | EXTENSIONS:
            hit = {"tactic": word, "line": line}
            if word == "simp":
                hit["form"] = "simp only" if simp_only_after(masked, match.end()) else "simp other"
            hits.append(hit)
        previous, last_end, last_pos = word, match.end(), match.start()
    return hits


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def rows(path: Path):
    with path.open() as stream:
        for line in stream:
            if line.strip():
                yield json.loads(line)


def write_json(path: Path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def category(name: str) -> str:
    return "term_or_tactic" if name in AMBIGUOUS else "branch_structure" if name in BRANCH else "conv_control" if name in CONV else "tactic_wrapper" if name in WRAPPERS else "tactic_candidate"


@dataclass
class Aggregate:
    declarations: int = 0
    proof_characters: int = 0
    zero_hits: int = 0
    occurrences: Counter = field(default_factory=Counter)
    presence: Counter = field(default_factory=Counter)
    pairs: Counter = field(default_factory=Counter)
    forms: Counter = field(default_factory=Counter)
    form_presence: Counter = field(default_factory=Counter)
    styles: Counter = field(default_factory=Counter)
    kinds: Counter = field(default_factory=Counter)
    modules: set = field(default_factory=set)

    def add(self, record: dict, hits: list[dict]):
        self.declarations += 1
        self.proof_characters += len(record["proof"])
        self.styles[record["proof_style"]] += 1
        self.kinds[record["declaration_kind"]] += 1
        self.modules.add(record["file_path"])
        count = Counter(hit["tactic"] for hit in hits)
        self.zero_hits += not bool(count)
        self.occurrences.update(count)
        self.presence.update(count.keys())
        self.pairs.update(combinations(sorted(count), 2))
        forms = Counter(hit["form"] for hit in hits if "form" in hit)
        self.forms.update(forms)
        self.form_presence.update(forms.keys())

    def metrics(self, occurrences: Counter, presence: Counter) -> list[dict]:
        return [{"name": name, "category": category(name), "occurrences": count,
                 "declarations": presence[name],
                 "prevalence_percent": round(100 * presence[name] / self.declarations, 4),
                 "occurrences_per_100_declarations": round(100 * count / self.declarations, 4)}
                for name, count in sorted(occurrences.items(), key=lambda kv: (-kv[1], kv[0]))]

    def summary(self):
        return {"declarations": self.declarations, "files_with_declarations": len(self.modules),
                "proof_characters": self.proof_characters,
                "proof_styles": dict(sorted(self.styles.items())),
                "declaration_kinds": dict(sorted(self.kinds.items())),
                "declarations_without_recognized_heads": self.zero_hits,
                "head_occurrences": sum(self.occurrences.values()),
                "heads": self.metrics(self.occurrences, self.presence),
                "simp_forms": self.metrics(self.forms, self.form_presence),
                "cooccurrence": [{"heads": list(pair), "declarations": count,
                                  "prevalence_percent": round(100 * count / self.declarations, 4)}
                                 for pair, count in sorted(self.pairs.items(), key=lambda kv: (-kv[1], kv[0]))]}


def subset_names(record: dict, verified_ids: set[str]):
    yield "all"
    if not record["contains_sorry"]:
        yield "no_direct_sorry"
    if record["proof_style"] == "by":
        yield "by_style"
    yield "native_ast" if record["native_parser_complete"] else "layout_recovered"
    if record["id"] in verified_ids:
        yield "kernel_verified_strata"


def collect(path: Path, verified_ids: set[str], output) -> dict:
    aggregates: dict[str, Aggregate] = {}
    baseline_aggregates: dict[str, Aggregate] = {}
    seen = set()
    versions = set()
    stored_counter_mismatches = 0
    for record in rows(path):
        if record["id"] in seen:
            raise ValueError(f"Duplicate declaration ID: {record['id']}")
        seen.add(record["id"])
        proof_hash = hashlib.sha256(record["proof"].encode()).hexdigest()
        if proof_hash != record["proof_sha256"]:
            raise ValueError(f"Proof hash mismatch: {record['id']}")
        baseline_hits = tactic_heads(record["proof"])
        hits = extended_heads(record["proof"])
        count = Counter(hit["tactic"] for hit in hits)
        baseline_count = Counter(hit["tactic"] for hit in baseline_hits)
        stored_counter_mismatches += dict(baseline_count) != record.get("approximate_tactic_heads", {})
        names = list(subset_names(record, verified_ids))
        for name in names:
            aggregates.setdefault(name, Aggregate()).add(record, hits)
            baseline_aggregates.setdefault(name, Aggregate()).add(record, baseline_hits)
        versions.add(json.dumps(record["version_info"], sort_keys=True))
        output.write(json.dumps({"id": record["id"], "source": record["source"],
            "name": record["name"], "file_path": record["file_path"], "source_link": record["source_link"],
            "proof_style": record["proof_style"], "proof_sha256": proof_hash,
            "contains_sorry": record["contains_sorry"], "subsets": names,
            "extraction_method": record.get("extraction_method", "native_lean_ast"),
            "heads": dict(count), "baseline_heads": dict(baseline_count), "simp_forms": dict(Counter(h["form"] for h in hits if "form" in h)),
            "hits": hits}, ensure_ascii=False) + "\n")
    return {"version_info": [json.loads(v) for v in sorted(versions)],
            "stored_counter_mismatches": stored_counter_mismatches,
            "subsets": {key: value.summary() for key, value in aggregates.items()},
            "baseline_subsets": {key: value.summary() for key, value in baseline_aggregates.items()}}


def mapping(summary: dict) -> dict:
    return {row["name"]: row for row in summary["heads"]}


def comparison(sources: dict) -> list[dict]:
    a, b = (mapping(sources[name]["subsets"]["all"]) for name in ("strata", "physlib"))
    result = []
    for name in sorted(a.keys() | b.keys()):
        pa, pb = (table.get(name, {}).get("prevalence_percent", 0) for table in (a, b))
        result.append({"name": name, "category": category(name), "strata": a.get(name), "physlib": b.get(name),
                       "strata_minus_physlib_percentage_points": round(pa-pb, 4),
                       "strata_to_physlib_prevalence_ratio": round(pa/pb, 4) if pb else None})
    return result


def report(data: dict) -> str:
    sources = data["sources"]
    a, b = (sources[name]["subsets"]["all"] for name in ("strata", "physlib"))
    out = ["# Strata·PhysLib 추출 증명의 tactic 빈도 비교", "",
        "추출한 `proof` 문자열만 대상으로 같은 정적 카운터를 적용했다. 표는 기존 pilot 카운터에 두 코퍼스에서 확인한 tactic 목록과 projection 오탐 보정을 적용한 **확장 카운터** 기준이다. 기존 baseline도 JSON에 그대로 보존했다. **실제 실행 횟수·heartbeat·성능 통계가 아니다.** `def`, `instance`, `example` 및 라이브러리 전체 코드는 분모에 포함하지 않았다.", "",
        "| 대상 | 추출 정리 | 정리가 있는 파일 | by 증명 | 항 증명 | 패턴 방정식 | 구조 증명 | 직접 sorry 제외 |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for source, s in sources.items():
        x = s["subsets"]["all"]
        out.append(f"| {source} | {x['declarations']:,} | {x['files_with_declarations']} | {x['proof_styles'].get('by',0):,} | {x['proof_styles'].get('term',0):,} | {x['proof_styles'].get('equations',0):,} | {x['proof_styles'].get('structure',0):,} | {s['subsets']['no_direct_sorry']['declarations']:,} |")
    ma, mb = mapping(a), mapping(b)
    out += ["", "## 먼저 보이는 차이", "",
        f"- Strata는 `simp_all`({ma['simp_all']['prevalence_percent']:.1f}%)·`induction`({ma['induction']['prevalence_percent']:.1f}%)·`cases`({ma['cases']['prevalence_percent']:.1f}%)가 많은 정리에 등장한다. PhysLib의 같은 출현률은 각각 {mb['simp_all']['prevalence_percent']:.1f}%·{mb['induction']['prevalence_percent']:.1f}%·{mb['cases']['prevalence_percent']:.1f}%다.",
        f"- PhysLib는 `rw`({mb['rw']['prevalence_percent']:.1f}%)·`ext`({mb['ext']['prevalence_percent']:.1f}%)·`fun_prop`({mb['fun_prop']['prevalence_percent']:.1f}%)가 상대적으로 두드러진다. Strata는 각각 {ma['rw']['prevalence_percent']:.1f}%·{ma['ext']['prevalence_percent']:.1f}%·0%다."]
    only_a, only_b = ({r['name']:r for r in summary['simp_forms']}['simp only']['occurrences'] for summary in (a,b))
    out += [f"- `simp` 등장 중 `only` 형태는 Strata {only_a:,}/{ma['simp']['occurrences']:,}회({100*only_a/ma['simp']['occurrences']:.1f}%), PhysLib {only_b:,}/{mb['simp']['occurrences']:,}회({100*only_b/mb['simp']['occurrences']:.1f}%)다. 이는 사용 형태의 차이이며 비용 차이를 의미하지 않는다."]
    out += ["", "## 주요 tactic 후보", "",
        "각 셀은 **소스 등장 횟수 / 사용 정리 수 (전체 정리 대비 출현률)**다. 한 정리에서 같은 tactic을 여러 번 쓰면 등장 횟수는 늘지만 사용 정리 수는 한 번만 센다. `<;>`로 여러 목표에 실행되어도 소스에 한 번 쓰였으면 한 번이다. 크기가 다른 코퍼스는 출현률로 비교한다.", "",
        "`have`, `show`, `calc`, `rfl` 등 term 겸용 head와 `case`·`next` branch 구조, `conv` 계열 제어 head는 아래 별도 표로 옮겼다.", "",
        "| 후보 head | Strata 횟수 / 정리 (%) | PhysLib 횟수 / 정리 (%) |", "| --- | ---: | ---: |"]
    maps = [mapping(a), mapping(b)]
    names = set()
    for summary in (a,b):
        names.update(x["name"] for x in [r for r in summary["heads"] if r["category"] == "tactic_candidate"][:12])
    names = sorted(names, key=lambda n: -max(m.get(n,{}).get("prevalence_percent",0) for m in maps))
    def cell(table, name):
        row = table.get(name)
        return "0 / 0 (0%)" if row is None else f"{row['occurrences']:,} / {row['declarations']:,} ({row['prevalence_percent']:.1f}%)"
    for name in names:
        out.append(f"| `{name}` | {cell(maps[0],name)} | {cell(maps[1],name)} |")
    out += ["", "## term 겸용 표기와 branch 구조", "",
            "이 표는 tactic과 term을 의미적으로 구별하지 않은 문자열 후보다. 예를 들어 `:= rfl`도 카운터가 감지한다. 합계를 순수 tactic 횟수로 해석하면 안 된다.", "",
            "| head | 분류 | Strata 횟수 / 정리 (%) | PhysLib 횟수 / 정리 (%) |", "| --- | --- | ---: | ---: |"]
    for name in sorted(AMBIGUOUS | BRANCH | CONV | WRAPPERS):
        out.append(f"| `{name}` | {category(name)} | {cell(maps[0],name)} | {cell(maps[1],name)} |")
    out += ["", "term/tactic 겸용 문법 전체를 완전하게 셈한 표는 아니다. `conv` 블록 안의 `rw`, `simp` 등도 같은 이름으로 세며, `enter`는 conv 제어 후보로 별도 구분했다.", "", "## simp 형태", "",
            "| 형태 | Strata 횟수 / 정리 (%) | PhysLib 횟수 / 정리 (%) |", "| --- | ---: | ---: |"]
    for name in ("simp only", "simp other"):
        out.append(f"| `{name}` | {cell({r['name']:r for r in a['simp_forms']},name)} | {cell({r['name']:r for r in b['simp_forms']},name)} |")
    out += ["", "`simp_all`, `simpa`, `dsimp`은 `simp`와 합치지 않았다. 두 simp 형태를 한 정리에서 모두 쓰면 사용 정리 수는 서로 겹칠 수 있다. 확장판은 `simp +contextual only`, `simp (disch := fun_prop) only`처럼 옵션 뒤에 있는 `only`도 인식한다. 기존 baseline은 즉시 뒤의 `only`만 인식하며 JSON에 보존했다.", "", "## 표본 선택에 따른 출현률", "",
            "각 열은 해당 하위집합 전체를 분모로 사용한다. `native_ast`/`layout_recovered`는 선언 경계 추출 방법이며 tactic AST 검증을 뜻하지 않는다. 직접 sorry 제외와 커널 검증은 서로 다른 조건이다.", "",
            "| 출처·하위집합 | 분모 | simp | rw | apply | exact | simp_all |", "| --- | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for source, s in sources.items():
        for subset, summary in s["subsets"].items():
            m = mapping(summary)
            out.append(f"| {source} / {subset} | {summary['declarations']:,} | " + " | ".join(f"{m.get(t,{}).get('prevalence_percent',0):.1f}%" for t in ("simp","rw","apply","exact","simp_all")) + " |")
    out += ["", "## 정리 단위 동시 출현", "", "두 후보가 같은 증명에 등장한 정리 수다. 실행 순서·의존 관계는 알 수 없다. term 겸용 및 branch 구조는 이 표에서 제외했다.", "", "| 출처 | 후보 쌍 | 정리 수 | 해당 코퍼스 비율 |", "| --- | --- | ---: | ---: |"]
    for source, s in sources.items():
        pairs = [p for p in s["subsets"]["all"]["cooccurrence"] if all(category(h)=="tactic_candidate" for h in p["heads"])][:5]
        for pair in pairs:
            out.append(f"| {source} | {' + '.join('`'+h+'`' for h in pair['heads'])} | {pair['declarations']:,} | {pair['prevalence_percent']:.1f}% |")
    out += ["", "## 해석 범위와 재현", "",
        "- 기존 `scripts/survey.py::tactic_heads` baseline과 확장 카운터를 각각 두 코퍼스에 동일하게 적용했다. 주석·문자열은 제외하며, 줄 시작과 `by`, `<;>`, `;`, `=>` 등의 뒤에서 allowlist에 있는 head를 찾는다. 확장판은 `fun_prop`, `fin_cases`, `erw` 등 관찰된 후보를 추가하고 `(term).right`와 같은 projection 오탐을 보정했다.",
        "- 실제 Lean tactic AST가 아니다. term 구문이나 syntax quotation이 섞이면 오탐할 수 있고, allowlist에 없는 사용자 정의 tactic·새 tactic·일부 modifier 변형은 누락된다. 기존 `try`, `repeat` 등 combinator는 세지 않으며, 확장판 `with_unfolding_all`·`solve`는 wrapper로 별도 표시한다. JSON의 전체 head 합계에는 이러한 구분된 후보도 포함된다.",
        "- `by_style`도 내부 term이 있을 수 있어 순수 tactic AST 통계가 아니다. 감지된 head가 0개인 증명도 분모에서 제외하지 않는다.",
        "- PhysLib는 6,755개 native AST 추출과 2,253개 layout 복원 증명을 함께 포함한다. PhysLib 커널·공리 검증은 미실시이며, Strata 검증 601개는 별도 하위집합으로 제공한다.",
        "- 빈도가 높은 tactic이 느리다는 뜻은 아니다. heartbeat 비용, 최적화 우선순위, 실행 중 목표 수는 이후 별도 측정해야 한다.",
        "- `summary.json`의 `subsets`는 확장판, `baseline_subsets`는 기존판 전체 head와 하위집합·동시출현 통계다. `declarations.jsonl`은 선언별 두 카운터의 head·확장판 증명 상대 줄 번호·원문 링크를 제공한다. 입력·스크립트 SHA-256과 allowlist는 summary에 기록했다.", "",
        "```bash", "source /Users/jwkweon/00_work/00_project/env/use.sh 05_pseudolab/LeanAgent-LeanRefactorArena", "python3 scripts/compare_tactics.py", "PYTHONPATH=scripts python3 -m unittest discover -s tests -p test_compare_tactics.py -v", "```", ""]
    return "\n".join(out)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path, default=ROOT / "results/tactic_comparison")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    verified_paths = [args.root / "strata" / name for name in ("verified_benchmark.jsonl", "verified_equations.jsonl")]
    verified_ids = {row["id"] for path in verified_paths for row in rows(path)}
    inputs = [args.root / source / "inventory.jsonl" for source in ("strata", "physlib")]
    verified_manifest = json.loads((args.root / "strata/verified_manifest.json").read_text())
    if sha256(inputs[0]) != verified_manifest["input_inventory_sha256"]:
        raise ValueError("Strata verified evidence does not match inventory hash")
    with (args.output / "declarations.jsonl").open("w") as output:
        sources = {source: collect(path, verified_ids if source == "strata" else set(), output)
                   for source, path in zip(("strata", "physlib"), inputs)}
    data = {"schema_version": 1, "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "method": "extended lexical allowlist with projection correction; survey.tactic_heads baseline retained; proof field only; not tactic AST or execution count",
            "denominator": "all declarations in each named subset, including zero recognized heads",
            "heartbeat_measured": False, "baseline_allowlist": sorted(TACTICS), "extended_allowlist": sorted(TACTICS | EXTENSIONS), "unreported_combinators": sorted(COMBINATORS),
            "ambiguous_term_heads": sorted(AMBIGUOUS), "branch_structure_heads": sorted(BRANCH), "conv_control_heads": sorted(CONV), "wrapper_heads": sorted(WRAPPERS),
            "inputs": {str(path.relative_to(args.root)): sha256(path) for path in inputs + verified_paths + [args.root / "strata/verified_manifest.json"]},
            "scripts": {str(path.relative_to(ROOT)): sha256(path) for path in (Path(__file__), ROOT / "scripts/survey.py")},
            "sources": sources, "comparison": comparison(sources)}
    write_json(args.output / "summary.json", data)
    (args.output / "report.md").write_text(report(data))
    print(json.dumps({name: {"declarations": info["subsets"]["all"]["declarations"],
                            "head_occurrences": info["subsets"]["all"]["head_occurrences"],
                            "stored_counter_mismatches": info["stored_counter_mismatches"]} for name, info in sources.items()}, indent=2))


if __name__ == "__main__":
    main()
