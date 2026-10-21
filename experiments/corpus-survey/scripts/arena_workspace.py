"""Historical tools operate only in an explicitly restored research workspace."""
import os
from pathlib import Path

value = os.environ.get("ARENA_CORPUS_WORKSPACE")
if not value or not (Path(value) / ".workspace.json").is_file():
    raise RuntimeError("Use scripts/corpus.py legacy --prepare, then legacy --script scripts/<name>.py")
ROOT = Path(value).resolve()
