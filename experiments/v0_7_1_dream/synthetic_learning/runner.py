import argparse,csv,json,time
from pathlib import Path
from .model import ChatModel
from .core import build_archive,observation_text,retrieve,build_replay_state,build_dream_state,load_or_build_cache,call_answer,score_answers,approx_tokens,query_memory_sections,bridge_coverage

METHODS=['no_memory','fact_rag','replay_only','dream_recombine','oracle_relevant','full_history']

def load_worlds(root):return [json.loads(p.read_text(encoding='utf-8')) for p in sorted((Path(root)/'synthetic_scenarios').glob('*.json'))]
def existing_keys(path):
    if not path.exists():return set()
    out=set()
    try:
        with path.open(newline='',encoding='utf-8') as f:
            for r in csv.DictReader(f):out.add((r['backend'],r['model'],r['scenario_id'],r['seed'],r['method'],r.get('distractors','')))
    except Exception:pass
    return out

def run_one(model,world,method,top_k,cache_dir,distractors):
    archive=build_archive(world,distractors);before=model.usage().copy();t0=time.time();cache_hit=False;ingest_s=0.0;bridge=0.0;bridge_details=[];idle_n=0
    if method=='no_memory':
        mem='No learned world rules are available.';diag={q['id']:[] for q in world['questions']}
    elif method=='full_history':
        mem='\n'.join(observation_text(o) for o in archive);diag={q['id']:['ALL'] for q in world['questions']}
    elif method=='oracle_relevant':
        byid={o['id']:o for o in world['observations']}
        sections=[];diag={}
        for q in world['questions']:
            ids=q.get('oracle_observation_ids',[])
            hits=[byid[i] for i in ids if i in byid]
            diag[q['id']]=[h['id'] for h in hits]
            sections.append(f"MEMORY AVAILABLE FOR {q['id']} (ORACLE RELEVANT):\n"+'\n'.join(observation_text(h) for h in hits))
        mem='\n\n'.join(sections)
    elif method=='fact_rag':
        mem,diag=query_memory_sections(world,archive,top_k)
    elif method=='replay_only':
        state,_=load_or_build_cache(cache_dir,'replay',model,world,distractors,lambda:build_replay_state(world,archive));cache_hit=True
        idle_n=len(state.get('selected_memories',[]));mem,diag=query_memory_sections(world,state.get('selected_memories',[]),top_k)
    elif method=='dream_recombine':
        ti=time.time();state,cache_hit=load_or_build_cache(cache_dir,'dream',model,world,distractors,lambda:build_dream_state(model,world,archive));ingest_s=time.time()-ti
        idle_n=len(state.get('selected_memories',[]));bridge,bridge_details=bridge_coverage(world,state)
        items=list(state.get('selected_memories',[]))+list(state.get('derived_relations',[]));mem,diag=query_memory_sections(world,items,top_k)
    else:raise ValueError(method)
    qt=time.time();data,raw,meta=call_answer(model,world,mem);query_s=time.time()-qt;score,details=score_answers(world,data,meta);after=model.usage().copy()
    return {'score':score,'details':details,'raw':raw,'parse_meta':meta,'memory_tokens_approx':approx_tokens(mem),'total_s':time.time()-t0,'query_s':query_s,'ingest_s':ingest_s,'cache_hit':cache_hit,'prompt_tokens':after['prompt_tokens']-before['prompt_tokens'],'completion_tokens':after['completion_tokens']-before['completion_tokens'],'calls':after['calls']-before['calls'],'retrieval':diag,'bridge_coverage':bridge,'bridge_details':bridge_details,'idle_selected_n':idle_n}

def main(argv=None):
    ap=argparse.ArgumentParser();ap.add_argument('--backend',default='mock',choices=['mock','ollama','openai_compat']);ap.add_argument('--model',default='mock');ap.add_argument('--base-url',default=None);ap.add_argument('--scenarios',default='2');ap.add_argument('--seeds',type=int,default=1);ap.add_argument('--methods',default=','.join(METHODS));ap.add_argument('--temperature',type=float,default=0.1);ap.add_argument('--top-k',type=int,default=2);ap.add_argument('--num-ctx',type=int,default=8192);ap.add_argument('--timeout',type=int,default=300);ap.add_argument('--distractors',type=int,default=80);ap.add_argument('--fresh',action='store_true');ap.add_argument('--pilot',action='store_true');args=ap.parse_args(argv)
    root=Path(__file__).resolve().parents[1];worlds=load_worlds(root)
    if args.pilot:args.scenarios='2';args.seeds=1;args.methods='no_memory,fact_rag,replay_only,dream_recombine,oracle_relevant,full_history';args.distractors=min(args.distractors,60)
    if args.scenarios!='all':worlds=worlds[:int(args.scenarios)]
    methods=[x.strip() for x in args.methods.split(',') if x.strip()];bad=[x for x in methods if x not in METHODS]
    if bad:raise SystemExit(f'Unknown methods: {bad}')
    out=root/'results'/'dream_runs.csv';out.parent.mkdir(exist_ok=True)
    if args.fresh and out.exists():out.unlink()
    keys=existing_keys(out);fields=['backend','model','scenario_id','scenario_name','seed','method','distractors','top_k','score','bridge_coverage','idle_selected_n','memory_tokens_approx','prompt_tokens','completion_tokens','calls','ingest_s','query_s','total_s','cache_hit','parse_ok','parse_mode','parse_error','missing_ids','retrieval_json','bridge_details_json','details_json','raw_answer'];wh=not out.exists()
    with out.open('a',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields)
        if wh:w.writeheader()
        for seed in range(args.seeds):
            model=ChatModel(args.backend,args.model,args.base_url,args.temperature,seed,max_tokens=500,timeout=args.timeout,num_ctx=args.num_ctx)
            for world in worlds:
                for method in methods:
                    key=(args.backend,args.model,world['id'],str(seed),method,str(args.distractors))
                    if key in keys:print('SKIP',world['id'],seed,method);continue
                    print('RUN ',world['id'],seed,method,flush=True);r=run_one(model,world,method,args.top_k,root/'results'/'cache',args.distractors);pm=r['parse_meta']
                    row={'backend':args.backend,'model':args.model,'scenario_id':world['id'],'scenario_name':world['name'],'seed':seed,'method':method,'distractors':args.distractors,'top_k':args.top_k,'score':round(r['score'],6),'bridge_coverage':round(r['bridge_coverage'],6),'idle_selected_n':r['idle_selected_n'],'memory_tokens_approx':r['memory_tokens_approx'],'prompt_tokens':r['prompt_tokens'],'completion_tokens':r['completion_tokens'],'calls':r['calls'],'ingest_s':round(r['ingest_s'],3),'query_s':round(r['query_s'],3),'total_s':round(r['total_s'],3),'cache_hit':r['cache_hit'],'parse_ok':pm.get('parse_ok'),'parse_mode':pm.get('parse_mode'),'parse_error':pm.get('parse_error'),'missing_ids':';'.join(pm.get('missing_ids',[])),'retrieval_json':json.dumps(r['retrieval'],ensure_ascii=False),'bridge_details_json':json.dumps(r['bridge_details'],ensure_ascii=False),'details_json':json.dumps(r['details'],ensure_ascii=False),'raw_answer':r['raw']}
                    w.writerow(row);f.flush();keys.add(key);print(f"  score={r['score']:.3f} bridge={r['bridge_coverage']:.3f} prompt={r['prompt_tokens']} query={r['query_s']:.1f}s",flush=True)
    print(f'\nSaved: {out}')
