import argparse,csv,json,time
from pathlib import Path
from .model import ChatModel
from .core import *

METHODS=['no_memory','no_seek','random_seek','generic_seek','gap_curiosity','oracle_seek_direct','oracle_seek_consolidated','oracle_relevant']

def load_worlds(root):
    return [json.loads(p.read_text(encoding='utf-8')) for p in sorted((root/'synthetic_curiosity_scenarios').glob('syn*.json'))]

def existing_keys(path):
    if not path.exists(): return set()
    with path.open(encoding='utf-8') as f:
        return {(r['backend'],r['model'],r['scenario_id'],r['seed'],r['method'],r['distractors'],r.get('curiosity_budget','')) for r in csv.DictReader(f)}

def run_one(model,world,method,top_k,cache_dir,distractors,seed,curiosity_budget,min_gap_confidence):
    t0=time.time();before=model.usage().copy();archive=build_archive(world,distractors)
    gapkey=cache_key('gap',model.model,seed,world['id'],distractors)
    gap_state,_=load_or_build(cache_dir,gapkey,lambda:build_gap_state(model,world,archive))
    gap_score,gap_details=gap_detection(world,gap_state)
    candidates=world['candidate_documents']; selected=[];selection_raw='';post_state={'selected_memories':gap_state.get('selected_memories',[]),'selected_documents':[],'derived_relations':[]};ingest_s=0.0
    eligible=eligible_gaps(gap_state,min_gap_confidence)

    if method=='no_memory':
        mem='No stored world memory.';retrieval={}
    elif method=='oracle_relevant':
        mem,retrieval=oracle_relevant_sections(world,candidates)
    else:
        ti=time.time()
        if method=='no_seek': selected=[]
        elif method=='random_seek': selected=select_random(world,candidates,seed,k=curiosity_budget)
        elif method=='generic_seek':
            skey=cache_key(f'generic_select_b{curiosity_budget}',model.model,seed,world['id'],distractors)
            val,_=load_or_build(cache_dir,skey,lambda:(lambda sr:{'selected':sr[0],'raw':sr[1]})(select_generic(model,world,gap_state,candidates,k=curiosity_budget)))
            selected=val.get('selected',[]);selection_raw=val.get('raw','')
        elif method=='gap_curiosity': selected=select_gap_curiosity(world,gap_state,candidates,budget=curiosity_budget,min_confidence=min_gap_confidence)
        elif method in ('oracle_seek_direct','oracle_seek_consolidated'):
            cmap={d['id']:d for d in candidates};selected=[]
            for q in world['questions']:
                d=dict(cmap[q['correct_document_id']])
                if d['id'] not in {x['id'] for x in selected}: selected.append(d)
            selected=selected[:curiosity_budget]

        if method=='oracle_seek_direct':
            mem,retrieval=direct_learned_sections(world,selected)
        else:
            if method!='no_seek':
                ids='-'.join(sorted(x['id'] for x in selected)) or 'none'
                pkey=cache_key('post_'+method+'_'+ids,model.model,seed,world['id'],distractors)
                post_state,_=load_or_build(cache_dir,pkey,lambda:build_post_learning_state(model,world,gap_state,selected))
            else:
                post_state={'selected_memories':gap_state.get('selected_memories',[]),'selected_documents':[],'derived_relations':gap_state.get('derived_relations',[])}
            items=list(post_state.get('selected_memories',[]))+list(post_state.get('selected_documents',[]))+list(post_state.get('derived_relations',[]))
            mem,retrieval=query_sections(world,items,top_k)
        ingest_s=time.time()-ti

    sel_recall,sel_precision,sel_hits=selection_metrics(world,selected)
    bridge,supported_bridge,bridge_details=bridge_coverage(world,post_state)
    qt=time.time();raw=model.chat(SYSTEM,answer_prompt(world,mem),max_tokens=240);query_s=time.time()-qt
    answers,parse_meta=parse_answers(raw,[q['id'] for q in world['questions']]);score,details=score_answers(world,answers);after=model.usage().copy()
    return {
        'score':score,'gap_detection':gap_score,'gap_details':gap_details,
        'selection_recall':sel_recall,'selection_precision':sel_precision,'selected_ids':[x['id'] for x in selected],'selection_hits':sel_hits,
        'bridge_coverage':bridge,'supported_bridge_coverage':supported_bridge,'bridge_details':bridge_details,
        'eligible_gap_count':len(eligible),'pursued_gap_count':len(selected),'budget_exhausted':len(eligible)>curiosity_budget,
        'memory_tokens_approx':approx_tokens(mem),'prompt_tokens':after['prompt_tokens']-before['prompt_tokens'],'completion_tokens':after['completion_tokens']-before['completion_tokens'],'calls':after['calls']-before['calls'],
        'gap_detection_mode':gap_state.get('gap_detection_mode','unknown'),'consolidation_mode':post_state.get('consolidation_mode','none'),'ingest_s':ingest_s,'query_s':query_s,'total_s':time.time()-t0,'parse_meta':parse_meta,'retrieval':retrieval,'details':details,'raw_answer':raw,'selection_raw':selection_raw
    }

def main(argv=None):
    ap=argparse.ArgumentParser();ap.add_argument('--backend',default='mock',choices=['mock','ollama','openai_compat']);ap.add_argument('--model',default='mock');ap.add_argument('--base-url',default=None);ap.add_argument('--scenarios',default='2');ap.add_argument('--seeds',type=int,default=1);ap.add_argument('--methods',default=','.join(METHODS));ap.add_argument('--temperature',type=float,default=0.1);ap.add_argument('--top-k',type=int,default=2);ap.add_argument('--num-ctx',type=int,default=8192);ap.add_argument('--timeout',type=int,default=300);ap.add_argument('--distractors',type=int,default=30);ap.add_argument('--curiosity-budget',type=int,default=3);ap.add_argument('--min-gap-confidence',type=float,default=0.50);ap.add_argument('--fresh',action='store_true');ap.add_argument('--pilot',action='store_true');args=ap.parse_args(argv)
    root=Path(__file__).resolve().parents[1];worlds=load_worlds(root)
    if args.pilot: args.scenarios='2';args.seeds=1;args.methods=','.join(METHODS);args.distractors=min(args.distractors,20)
    if args.scenarios!='all': worlds=worlds[:int(args.scenarios)]
    methods=[x.strip() for x in args.methods.split(',') if x.strip()]
    out=root/'results'/'curiosity_runs.csv';out.parent.mkdir(exist_ok=True)
    if args.fresh and out.exists():out.unlink()
    keys=existing_keys(out)
    fields=['backend','model','scenario_id','scenario_name','seed','method','distractors','top_k','curiosity_budget','min_gap_confidence','score','gap_detection','selection_recall','selection_precision','bridge_coverage','supported_bridge_coverage','eligible_gap_count','pursued_gap_count','budget_exhausted','gap_detection_mode','consolidation_mode','memory_tokens_approx','prompt_tokens','completion_tokens','calls','ingest_s','query_s','total_s','parse_ok','missing_ids','selected_ids','selection_hits','retrieval_json','gap_details_json','bridge_details_json','details_json','raw_answer','selection_raw']
    write_header=not out.exists()
    with out.open('a',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields)
        if write_header:w.writeheader()
        for seed in range(args.seeds):
            model=ChatModel(args.backend,args.model,args.base_url,args.temperature,seed,max_tokens=700,timeout=args.timeout,num_ctx=args.num_ctx)
            for world in worlds:
                for method in methods:
                    key=(args.backend,args.model,world['id'],str(seed),method,str(args.distractors),str(args.curiosity_budget))
                    if key in keys: print('SKIP',world['id'],seed,method);continue
                    print('RUN ',world['id'],seed,method,flush=True)
                    r=run_one(model,world,method,args.top_k,root/'results'/'cache',args.distractors,seed,args.curiosity_budget,args.min_gap_confidence)
                    row={'backend':args.backend,'model':args.model,'scenario_id':world['id'],'scenario_name':world['name'],'seed':seed,'method':method,'distractors':args.distractors,'top_k':args.top_k,'curiosity_budget':args.curiosity_budget,'min_gap_confidence':args.min_gap_confidence,'score':round(r['score'],6),'gap_detection':round(r['gap_detection'],6),'selection_recall':round(r['selection_recall'],6),'selection_precision':round(r['selection_precision'],6),'bridge_coverage':round(r['bridge_coverage'],6),'supported_bridge_coverage':round(r['supported_bridge_coverage'],6),'eligible_gap_count':r['eligible_gap_count'],'pursued_gap_count':r['pursued_gap_count'],'budget_exhausted':r['budget_exhausted'],'gap_detection_mode':r['gap_detection_mode'],'consolidation_mode':r['consolidation_mode'],'memory_tokens_approx':r['memory_tokens_approx'],'prompt_tokens':r['prompt_tokens'],'completion_tokens':r['completion_tokens'],'calls':r['calls'],'ingest_s':round(r['ingest_s'],3),'query_s':round(r['query_s'],3),'total_s':round(r['total_s'],3),'parse_ok':r['parse_meta']['parse_ok'],'missing_ids':';'.join(r['parse_meta']['missing_ids']),'selected_ids':';'.join(r['selected_ids']),'selection_hits':';'.join(r['selection_hits']),'retrieval_json':json.dumps(r['retrieval']),'gap_details_json':json.dumps(r['gap_details']),'bridge_details_json':json.dumps(r['bridge_details']),'details_json':json.dumps(r['details']),'raw_answer':r['raw_answer'],'selection_raw':r['selection_raw']}
                    w.writerow(row);f.flush();keys.add(key)
                    print(f"  score={r['score']:.3f} gap={r['gap_detection']:.3f} select={r['selection_recall']:.3f} bridge={r['supported_bridge_coverage']:.3f} eligible={r['eligible_gap_count']} pursued={r['pursued_gap_count']}",flush=True)
    print('\nSaved:',out)
