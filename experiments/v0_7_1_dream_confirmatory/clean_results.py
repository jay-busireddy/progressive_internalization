import argparse,shutil
from pathlib import Path
ap=argparse.ArgumentParser();ap.add_argument('--keep-cache',action='store_true');a=ap.parse_args();root=Path(__file__).resolve().parent/'results'
for p in [root/'dream_runs.csv',root/'dream_summary.md']:
    if p.exists():p.unlink();print('deleted',p)
if not a.keep_cache and (root/'cache').exists():shutil.rmtree(root/'cache');(root/'cache').mkdir(parents=True,exist_ok=True);print('cleared cache')
