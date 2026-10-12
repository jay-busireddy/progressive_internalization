from pathlib import Path
import pandas as pd

root=Path(__file__).resolve().parent
p=root/'results'/'curiosity_runs.csv'
if not p.exists(): raise SystemExit('No results/curiosity_runs.csv found')
df=pd.read_csv(p)
agg=df.groupby('method').agg(score=('score','mean'),gap_detection=('gap_detection','mean'),selection_recall=('selection_recall','mean'),selection_precision=('selection_precision','mean'),bridge=('supported_bridge_coverage','mean'),eligible=('eligible_gap_count','mean'),pursued=('pursued_gap_count','mean'),prompt=('prompt_tokens','mean'),query_s=('query_s','mean'),ingest_s=('ingest_s','mean')).round(3)
print(agg.to_string())

pivot=df.pivot_table(index=['scenario_id','seed'],columns='method',values='score',aggfunc='first')
def delta(a,b):
    if a not in pivot or b not in pivot:return None
    x=(pivot[a]-pivot[b]).dropna();return (float(x.mean()),int((x>1e-9).sum()),int((x.abs()<=1e-9).sum()),int((x<-1e-9).sum()))

def val(method,col,default=0.0):
    return float(agg.loc[method,col]) if method in agg.index else default

gap=val('gap_curiosity','gap_detection');sel=val('gap_curiosity','selection_recall');bridge=val('gap_curiosity','bridge')
nom=val('no_memory','score',1.0);oracle=val('oracle_relevant','score');direct=val('oracle_seek_direct','score');ocon=val('oracle_seek_consolidated','score')
rand=delta('gap_curiosity','random_seek');gen=delta('gap_curiosity','generic_seek');noseek=delta('gap_curiosity','no_seek')
valid=nom<=0.10 and oracle>=0.80 and direct>=0.80 and ocon>=0.80
if not valid: verdict='INVALID PIPELINE OR LEARNABILITY CONTROL'
elif gap>=0.75 and sel>=0.75 and bridge>=0.60 and rand and rand[0]>=0.15 and noseek and noseek[0]>=0.20:
    verdict='POSITIVE SYNTHETIC CURIOSITY MECHANISM'
    if gen and gen[0]>=0.05: verdict+='; GAP-DRIVEN ALSO BEATS GENERIC SEEKING'
    else: verdict+='; GAP-DRIVEN DOES NOT CLEAR GENERIC-SEEKING ADVANTAGE THRESHOLD'
else: verdict='NO STRONG CURIOSITY EFFECT'

lines=['# v0.7.2.2 Synthetic Curiosity Summary','',f'Rows analyzed: {len(df)}','']
for m,row in agg.iterrows():
    lines.append(f"- **{m}**: score {row.score:.3f}, gap {row.gap_detection:.3f}, select-recall {row.selection_recall:.3f}, supported-bridge {row.bridge:.3f}, eligible {row.eligible:.2f}, pursued {row.pursued:.2f}, prompt {row.prompt:.1f}, query {row.query_s:.1f}s, idle/ingest {row.ingest_s:.1f}s")
lines += ['',f'Validity: no_memory={nom:.3f}; oracle_relevant={oracle:.3f}; oracle_seek_direct={direct:.3f}; oracle_seek_consolidated={ocon:.3f}.',f'Gap-curiosity detection={gap:.3f}; selection recall={sel:.3f}; supported post-learning bridge={bridge:.3f}.']
for name,d in [('Gap - Random',rand),('Gap - Generic',gen),('Gap - NoSeek',noseek)]:
    if d:lines.append(f'{name}: delta {d[0]:+.3f}, wins/ties/losses={d[1]}/{d[2]}/{d[3]}')
lines += ['',f'**Verdict:** {verdict}.','', '## Per-world scores', pivot.reset_index().to_markdown(index=False)]
summary='\n'.join(lines);print('\n'+summary);(root/'results'/'curiosity_summary.md').write_text(summary,encoding='utf-8')
