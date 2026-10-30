import os,sys
from pathlib import Path
os.environ['ELAN_HOME']=sys.argv[1];os.environ['XDG_CACHE_HOME']=sys.argv[2]
lake=str(Path.home()/'.elan/bin/lake');os.execv(lake,[lake,'env','lean',*sys.argv[3:]])
