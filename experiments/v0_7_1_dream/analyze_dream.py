from pathlib import Path
import pandas as pd

def main():
    root=Path(__file__).resolve().parent;p=root/'results'/'dream_runs.csv'
    if not p.exists():raise SystemExit('No results/dream_runs.csv found')
    d=pd.read_csv(p)
    lines=['# v0.7.1 Idle Dream/Recombination Summary','',f'Rows analyzed: {len(d)}','']
    for m,g in d.groupby('method'):
        extra=(f", bridge {g.bridge_coverage.mean():.3f}" if m=='dream_recombine' else '')
        lines.append(f"- **{m}**: score {g.score.mean():.3f}, memory {g.memory_tokens_approx.mean():.1f}, prompt {g.prompt_tokens.mean():.1f}, query {g.query_s.mean():.1f}s, ingest {g.ingest_s.mean():.1f}s"+extra)
    means=d.groupby('method').score.mean().to_dict();no=means.get('no_memory',1);oracle=means.get('oracle_relevant',0);full=means.get('full_history',0);fact=means.get('fact_rag',0);rep=means.get('replay_only',0);dream=means.get('dream_recombine',0)
    paired=d.pivot_table(index=['scenario_id','seed'],columns='method',values='score',aggfunc='mean')
    wins=ties=losses=0;delta=0.0
    if {'dream_recombine','replay_only'}.issubset(paired.columns):
        dif=(paired.dream_recombine-paired.replay_only);wins=int((dif>1e-9).sum());ties=int((dif.abs()<=1e-9).sum());losses=int((dif<-1e-9).sum());delta=float(dif.mean())
    bridge=float(d.loc[d.method=='dream_recombine','bridge_coverage'].mean()) if (d.method=='dream_recombine').any() else 0.0
    valid=no<=0.10 and oracle>=0.80
    lines+=['',f'Validity: no_memory={no:.3f} (<=0.10), oracle_relevant={oracle:.3f} (>=0.80).',f'Full-history stress baseline: {full:.3f} (not a validity gate).',f'Dream - Fact-RAG: {dream-fact:+.3f}',f'Dream - Replay-only: {dream-rep:+.3f}',f'Dream vs Replay paired wins/ties/losses: {wins}/{ties}/{losses}',f'Mean Dream bridge coverage before query: {bridge:.3f}']
    if not valid:verdict='INVALID: leakage or oracle-relevant learnability gate failed.'
    elif dream-rep>=0.08 and wins>losses and bridge>=0.60:verdict='CONTINUE: offline recombination materially beats replay-only and formed pre-query bridges.'
    elif dream-rep<=0.03:verdict='STOP: offline recombination does not materially beat selective replay under the same retrieval budget.'
    else:verdict='AMBIGUOUS: inspect paired worlds; effect is between stop/continue thresholds.'
    lines+=['',f'**Verdict:** {verdict}','','## Per-world scores']
    tab=d.pivot_table(index='scenario_id',columns='method',values='score',aggfunc='mean').round(3);lines.append(tab.to_markdown())
    lines+=['','## No-memory leakage by world']
    if (d.method=='no_memory').any():
        for k,v in d[d.method=='no_memory'].groupby('scenario_id').score.mean().items():lines.append(f'- {k}: {v:.3f}')
    lines+=['','## Oracle-relevant learnability by world']
    if (d.method=='oracle_relevant').any():
        for k,v in d[d.method=='oracle_relevant'].groupby('scenario_id').score.mean().items():lines.append(f'- {k}: {v:.3f}')
    out=root/'results'/'dream_summary.md';out.write_text('\n'.join(lines),encoding='utf-8');print('\n'.join(lines));print(f'\nSaved: {out}')
if __name__=='__main__':main()
