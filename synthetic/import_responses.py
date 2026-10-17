"""Import a reviewed literal response envelope; never execute its Python code."""
import ast
import argparse
from pathlib import Path
from .common import rows, write
from .generation import submit


def import_responses(dataset, envelope):
    tree = ast.parse(Path(envelope).read_text(encoding='utf-8'))
    matches = [n for n in tree.body if isinstance(n, ast.Assign)
               and any(isinstance(t, ast.Name) and t.id == 'RESPONSES' for t in n.targets)]
    if len(matches) != 1: raise ValueError('Expected a single literal RESPONSES mapping')
    responses = ast.literal_eval(matches[0].value)
    names = {r['theorem_name']: r for r in rows(Path(dataset)/'theorems.jsonl')}
    for name, proofs in responses.items():
        if len(proofs) != 5: raise ValueError('Exactly five attempts required')
        for i, proof in enumerate(proofs, 1):
            candidate = names[name]['problem_id'] + f'-{i}'
            scratch = Path('.synthetic-cache') / 'response-import.txt'
            write(scratch, proof)
            submit(dataset, candidate, scratch)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--dataset', required=True)
    p.add_argument('--envelope', required=True)
    a = p.parse_args()
    import_responses(a.dataset, a.envelope)
