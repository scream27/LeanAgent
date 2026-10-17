"""Copy reviewable text evidence to a Git repository, excluding toolchains/binaries."""
from pathlib import Path
import shutil
import sys

HERE = Path(__file__).resolve().parent
DEST = Path(sys.argv[1]).resolve()
DEST.mkdir(parents=True, exist_ok=True)
root_suffixes = {'.py', '.md', '.json', '.jsonl', '.csv', '.txt'}
trees = {'reference', 'inputs', 'derived_candidates', 'runs', 'policy', 'setup_logs', 'instrumentation_smoke'}
count = 0
for src in HERE.iterdir():
    files = src.rglob('*') if src.name in trees and src.is_dir() else [src]
    for file in files:
        if not file.is_file():
            continue
        allowed = (file.suffix in root_suffixes or file.suffix == '.lean' or file.suffix == '.log'
                   or (src.name == 'reference' and file.name.startswith('LICENSE')))
        if not allowed:
            continue
        target = DEST / file.relative_to(HERE)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(file, target)
        count += 1
(DEST / '.gitignore').write_text('.venv/\nenvironments/\ntokenizer_cache/\n__pycache__/\n*.olean*\n*.ir\n*.ilean\n*.sig\n.DS_Store\n')
print(f'Exported {count} text artifacts to {DEST}')
