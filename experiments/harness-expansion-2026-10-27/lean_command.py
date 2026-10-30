"""Pinned isolated elan environment; no credentials or extra imports."""
import os,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;REPO=HERE.parents[1]
os.environ['ELAN_HOME']=str(REPO/'artifacts/harness-expansion/physlib-v4.32.0/elan')
os.environ['XDG_CACHE_HOME']=str(REPO/'artifacts/harness-expansion/physlib-v4.32.0/cache')
lake=str(Path.home()/'.elan/bin/lake')
os.execv(lake,[lake,'env','lean',*sys.argv[1:]])
