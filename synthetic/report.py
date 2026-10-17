"""Measured outcomes only; null is never counted as a zero measurement."""
from collections import Counter
from pathlib import Path
import statistics
from .common import rows, save, write

CATEGORIES = ['syntax_errors', 'unknown_identifiers', 'type_mismatches', 'unsolved_goals',
              'tactic_failures', 'resource_exhaustion', 'other_errors']
METRICS = ['reference_token_count', 'candidate_token_count', 'length_reduction_ratio']


def stats(values):
    values = [v for v in values if v is not None]
    if not values: return dict(n=0, mean=None, median=None, standard_deviation=None, min=None, max=None)
    return dict(n=len(values), mean=statistics.mean(values), median=statistics.median(values),
                standard_deviation=statistics.pstdev(values), min=min(values), max=max(values))


def summarize(data):
    n = len(data)
    compiled = sum(r['compile_success'] is True for r in data)
    failed = sum(r['compile_success'] is False for r in data)
    errors = Counter(r['error_category'] for r in data if r['compile_success'] is False)
    summary = dict(total_candidates=n, compiling=compiled, failing=failed,
        unverified=n-compiled-failed, compile_percentage=100*compiled/n if n else None,
        failure_percentage=100*failed/n if n else None,
        safety_violations=sum(r['safety_passed'] is False for r in data),
        duplicates=sum(r['duplicate_candidate'] for r in data),
        errors={k: errors[k] for k in CATEGORIES}, proof_lengths={}, theorems=[],
        heartbeat_usage=None, api_token_usage=None,
        length_reduction_definition='1 - candidate_token_count / reference_token_count; negative means longer',
        standard_deviation_definition='population',
        error_classification='First matching category by documented precedence; complete raw diagnostics retained')
    for label, group in [('all', data), ('compiling', [r for r in data if r['compile_success'] is True]),
                         ('failing', [r for r in data if r['compile_success'] is False])]:
        summary['proof_lengths'][label] = {m: stats([r[m] for r in group]) for m in METRICS}
    for name in sorted({r['theorem_name'] for r in data}):
        group = [r for r in data if r['theorem_name'] == name]
        summary['theorems'].append(dict(theorem_name=name, candidates=len(group),
            compile_success_rate=sum(r['compile_success'] is True for r in group)/len(group),
            unique_candidates=len({r['candidate_proof'] for r in group}),
            mean_length_reduction=statistics.mean(r['length_reduction_ratio'] for r in group)))
    return summary


def report(dataset):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    data = rows(dataset / 'dataset.jsonl')
    summary = summarize(data)
    save(dataset / 'summary.json', summary)
    charts = dataset / 'charts'
    charts.mkdir(exist_ok=True)
    plt.rcParams.update({'figure.dpi': 140, 'axes.spines.top': False, 'axes.spines.right': False})
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(['Compiling', 'Failed'], [summary['compiling'], summary['failing']], color=['#17856c', '#d86651'])
    ax.set(ylabel='Candidates', title='Lean compilation outcomes')
    fig.tight_layout(); fig.savefig(charts / 'compilation.png'); plt.close(fig)
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.bar([c.replace('_', '\n') for c in CATEGORIES], [summary['errors'][c] for c in CATEGORIES], color='#577eac')
    ax.set(ylabel='Candidates', title='Primary compiler error categories')
    fig.tight_layout(); fig.savefig(charts / 'errors.png'); plt.close(fig)
    fig, ax = plt.subplots(figsize=(7, 4))
    reductions = [r['length_reduction_ratio'] for r in data]
    low, high = min(reductions), max(reductions)
    if low == high: low, high = low-.05, high+.05
    bins = [low + (high-low)*i/10 for i in range(11)]
    for label, flag, color in [('Compiling', True, '#17856c'), ('Failed', False, '#d86651')]:
        vals = [r['length_reduction_ratio'] for r in data if r['compile_success'] is flag]
        if vals: ax.hist(vals, bins=bins, alpha=.65, label=label, color=color)
    ax.set(xlabel='1 − candidate / reference tokens', ylabel='Candidates', title='Proof length reduction')
    ax.legend(); fig.tight_layout(); fig.savefig(charts / 'length-reduction.png'); plt.close(fig)
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.barh([r['theorem_name'] for r in summary['theorems']],
            [100*r['compile_success_rate'] for r in summary['theorems']], color='#17856c')
    ax.set(xlim=(0, 100), xlabel='Compiling candidates (%)', title='Per-theorem compilation')
    fig.tight_layout(); fig.savefig(charts / 'per-theorem.png'); plt.close(fig)
    lines = ['# Strata synthetic proof dataset', '',
        f"Generated **{summary['total_candidates']}** first-attempt candidates: **{summary['compiling']}** compiling "
        f"({summary['compile_percentage']:.1f}%), **{summary['failing']}** failed ({summary['failure_percentage']:.1f}%).",
        f"Safety violations: {summary['safety_violations']}. Exact duplicate attempts beyond the first: {summary['duplicates']}.", '',
        'All reference proofs were compiled first. The 15-candidate pilot preceded the remaining 35 candidates. '
        'Failures and duplicates were retained without retries or repairs.', '',
        '## Measurement limits', '',
        'Generation used the user-authorized shared Codex session, with five fixed refactoring objectives. '
        'These are separate first-response attempts, but they are **not statistically independent API samples**. '
        'The exact model deployment, temperature, seed, prompt/completion API tokens, and heartbeat usage are unavailable (null). '
        'No costs are estimated. Lexical proof tokens use the pinned upstream Arena tokenizer, not LLM tokens. '
        'Compilation success and safety are separate labels. For noncompiling proofs, safety records lexical checks; '
        'transitive axiom status is unavailable. This small, shortest-eligible-first sample is not representative of all Strata.', '',
        '## Error distribution', '', '| Category | Count |', '|---|---:|']
    lines += [f"| {k} | {v} |" for k, v in summary['errors'].items()]
    lines += ['', 'Categories come from actual compiler diagnostics. Precedence: resource exhaustion, syntax, '
              'unknown identifiers, type mismatches, unsolved goals, tactic failures, other. '
              'A candidate with several diagnostics receives one primary label; raw logs permit reclassification.', '',
              '## Proof lengths', '', 'Reduction = 1 − candidate/reference. Standard deviation is population standard deviation. '
              'Reference lengths below are weighted by candidate attempts.', '',
              '| Group | Metric | Mean | Median | Std. dev. | Min | Max |', '|---|---|---:|---:|---:|---:|---:|']
    for label, metrics in summary['proof_lengths'].items():
        for metric, values in metrics.items():
            numbers = ['unavailable' if values[k] is None else f'{values[k]:.4f}' for k in ['mean', 'median', 'standard_deviation', 'min', 'max']]
            lines.append(f"| {label} | {metric} | " + ' | '.join(numbers) + ' |')
    lines += ['', '## Theorems', '', '| Theorem | Candidates | Compile rate | Unique | Mean reduction |', '|---|---:|---:|---:|---:|']
    lines += [f"| {r['theorem_name']} | {r['candidates']} | {100*r['compile_success_rate']:.0f}% | {r['unique_candidates']} | {r['mean_length_reduction']:.4f} |" for r in summary['theorems']]
    lines += ['', '## Charts', '']
    for name in ['compilation', 'errors', 'length-reduction', 'per-theorem']:
        lines += [f'![{name}](charts/{name}.png)', '']
    write(dataset / 'report.md', '\n'.join(lines))
