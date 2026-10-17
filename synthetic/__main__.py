import argparse
from pathlib import Path
from .mining import mine
from .generation import prepare, submit, evaluate, review_pilot


def main():
    p = argparse.ArgumentParser(description='Reference-conditioned Lean synthetic proof dataset')
    sub = p.add_subparsers(dest='command', required=True)
    m = sub.add_parser('mine')
    m.add_argument('--repo', required=True)
    m.add_argument('--upstream', required=True)
    m.add_argument('--warmup', action='append', required=True)
    m.add_argument('--output', required=True)
    for name in ('prepare', 'verify', 'review-pilot', 'report', 'validate', 'reclassify'):
        c = sub.add_parser(name)
        c.add_argument('--dataset', required=True)
        if name in ('prepare', 'verify'): c.add_argument('--phase', choices=['pilot', 'remaining'], required=True)
        if name == 'verify':
            c.add_argument('--repo', required=True)
            c.add_argument('--upstream', required=True)
        if name == 'validate': c.add_argument('--upstream', required=True)
    c = sub.add_parser('submit')
    c.add_argument('--dataset', required=True)
    c.add_argument('--candidate-id', required=True)
    c.add_argument('--proof-file', required=True)
    a = p.parse_args()
    if a.command == 'mine': mine(a.repo, a.upstream, a.warmup, a.output)
    elif a.command == 'prepare': prepare(a.dataset, a.phase)
    elif a.command == 'submit': submit(a.dataset, a.candidate_id, a.proof_file)
    elif a.command == 'verify': evaluate(a.dataset, a.repo, a.upstream, a.phase)
    elif a.command == 'review-pilot': review_pilot(a.dataset)
    elif a.command == 'validate':
        from .validate import validate
        print(validate(a.dataset, a.upstream))
    elif a.command == 'reclassify':
        from .validate import reclassify
        reclassify(a.dataset)
    elif a.command == 'report':
        from .report import report
        report(Path(a.dataset))


if __name__ == '__main__': main()
