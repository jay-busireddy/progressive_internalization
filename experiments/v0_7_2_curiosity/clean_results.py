from pathlib import Path
import argparse,shutil
ap=argparse.ArgumentParser();ap.add_argument('--keep-cache',action='store_true');a=ap.parse_args();r=Path(__file__).resolve().parent/'results'
for n in ['curiosity_runs.csv','curiosity_summary.md']:
    p=r/n
    if p.exists():p.unlink()
if not a.keep_cache:
    c=r/'cache'
    if c.exists():shutil.rmtree(c)
    c.mkdir(parents=True,exist_ok=True)
print('Curiosity results cleaned' + ('; cache preserved' if a.keep_cache else ''))
