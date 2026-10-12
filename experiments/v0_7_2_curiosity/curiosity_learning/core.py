import json, re, hashlib, random
from collections import defaultdict
from pathlib import Path

SYSTEM = """You are learning an invented synthetic world. Opaque symbols have no meaning except what the supplied observations establish. Never use outside knowledge or real-world analogies. Respect source authority. Do not invent missing transitions. Future task questions are NOT available during idle learning or curiosity."""
AUTHORITY={"rumor":1,"poster":1,"casual_note":2,"field_note":2,"lesson":4,"official_manual":5,"official_revision":6}
OPAQUE_RE=re.compile(r'\b[A-Z]{3}-\d{2}\b')
PROCESS_RE=re.compile(r'\bPRC-\d{2}\b')
STAGE_RE=re.compile(r'\b(PRC-\d{2})\s+stage\s+(\d+)\s*,\s*([A-Z]{3}-\d{2})\s+changes\s+into\s+(?:terminal\s+marker\s+)?([A-Z]{3}-\d{2})', re.I)
COUNT_RE=re.compile(r'\b(PRC-\d{2})\s+contains\s+exactly\s+(\w+)\s+ordered\s+transitions', re.I)
DOC_STAGE_RE=re.compile(r'\bstage-(\d+)\s+(?:revision|note)\s+for\s+(PRC-\d{2})\s*:\s*([A-Z]{3}-\d{2})\s+changes\s+into\s+([A-Z]{3}-\d{2})', re.I)
RUMOR_STAGE_RE=re.compile(r'\b(PRC-\d{2})\s+stage\s+(\d+)\s*:\s*([A-Z]{3}-\d{2})\s+changes\s+into\s+([A-Z]{3}-\d{2})', re.I)
NUMBER_WORDS={'one':1,'two':2,'three':3,'four':4,'five':5,'six':6,'seven':7,'eight':8,'nine':9,'ten':10}


def approx_tokens(text): return max(1,len(str(text).split()))
def opaque_tokens(text): return set(OPAQUE_RE.findall(str(text).upper()))
def observation_text(o): return f"[{o['id']}] source={o.get('source','field_note')} authority={AUTHORITY.get(o.get('source','field_note'),2)} :: {o.get('text','')}"

def parse_json(raw, default=None):
    try: return json.loads(raw)
    except Exception: pass
    s=str(raw).strip()
    starts=[i for i,c in enumerate(s) if c=='{']
    for st in starts:
        cand=s[st:]
        if cand.count('[')>cand.count(']'): cand += ']'*(cand.count('[')-cand.count(']'))
        if cand.count('{')>cand.count('}'): cand += '}'*(cand.count('{')-cand.count('}'))
        try: return json.loads(cand)
        except Exception: pass
    return default

def _obs_graph(observations):
    toks=[opaque_tokens(o.get('text','')) for o in observations]
    token_to_idx=defaultdict(list)
    for i,ts in enumerate(toks):
        for t in ts: token_to_idx[t].append(i)
    adj=[set() for _ in observations]
    for inds in token_to_idx.values():
        for i in inds:
            for j in inds:
                if i!=j: adj[i].add(j)
    return adj

def select_replay_groups(observations,min_group=3,max_groups=8,max_group_size=12):
    adj=_obs_graph(observations);seen=set();groups=[]
    for i in range(len(observations)):
        if i in seen: continue
        stack=[i];seen.add(i);comp=[]
        while stack:
            u=stack.pop();comp.append(u)
            for v in adj[u]:
                if v not in seen: seen.add(v);stack.append(v)
        if len(comp)>=min_group:
            groups.append([observations[x] for x in comp[:max_group_size]])
    groups.sort(key=lambda g:(sum(AUTHORITY.get(x.get('source','field_note'),2) for x in g),len(g)), reverse=True)
    return groups[:max_groups]

def build_archive(world,distractors=30):
    obs=[dict(x) for x in world['observations']]
    seed=int(world.get('world_seed',1))
    for i in range(distractors):
        obs.append({"id":f"z{i:03d}","source":"field_note","text":f"Archive note {i}: isolated token X{seed:02d}{i:03d} is adjacent to Y{seed:02d}{i:03d}; no stage or transformation rule is stated."})
    rnd=random.Random(seed+distractors);rnd.shuffle(obs);return obs


def parse_transition(observation):
    """Parse one explicit synthetic stage transition without using future questions."""
    text=observation.get('text','')
    m=STAGE_RE.search(text)
    if m:
        process,stage,fr,to=m.group(1),m.group(2),m.group(3),m.group(4)
    else:
        m=DOC_STAGE_RE.search(text)
        if m:
            stage,process,fr,to=m.group(1),m.group(2),m.group(3),m.group(4)
        else:
            m=RUMOR_STAGE_RE.search(text)
            if not m: return None
            process,stage,fr,to=m.group(1),m.group(2),m.group(3),m.group(4)
    return {
        'process':process.upper(),
        'stage':int(stage),
        'from_symbol':fr.upper(),
        'to_symbol':to.upper(),
        'evidence_id':observation['id'],
        'source':observation.get('source','field_note'),
        'authority':AUTHORITY.get(observation.get('source','field_note'),2),
    }

def parse_process_count(observation):
    m=COUNT_RE.search(observation.get('text',''))
    if not m: return None
    raw=m.group(2).lower()
    try: count=int(raw)
    except Exception: count=NUMBER_WORDS.get(raw)
    if not count: return None
    return {
        'process':m.group(1).upper(), 'expected_stages':int(count),
        'evidence_id':observation['id'],
        'source':observation.get('source','field_note'),
        'authority':AUTHORITY.get(observation.get('source','field_note'),2),
    }

def build_process_models(observations):
    """Build an inspectable process graph from explicit observations only.

    This is deliberately deterministic: curiosity should be triggered by an actual
    incompleteness in the stored model, not by whether an LLM happens to phrase a
    missing link correctly.
    """
    models={}
    for o in observations:
        cnt=parse_process_count(o)
        if cnt:
            pm=models.setdefault(cnt['process'],{'process':cnt['process'],'expected_stages':None,'declaration_id':None,'known_steps':[]})
            if pm['expected_stages'] is None or cnt['authority'] >= pm.get('declaration_authority',-1):
                pm['expected_stages']=cnt['expected_stages'];pm['declaration_id']=cnt['evidence_id'];pm['declaration_authority']=cnt['authority']
        tr=parse_transition(o)
        if tr:
            pm=models.setdefault(tr['process'],{'process':tr['process'],'expected_stages':None,'declaration_id':None,'known_steps':[]})
            pm['known_steps'].append(tr)
    # Resolve competing claims about the same stage by source authority.
    for pm in models.values():
        by_stage={}
        for step in pm['known_steps']:
            cur=by_stage.get(step['stage'])
            if cur is None or (step['authority'],step['evidence_id']) > (cur['authority'],cur['evidence_id']):
                by_stage[step['stage']]=step
        pm['known_steps']=[by_stage[k] for k in sorted(by_stage)]
        pm.pop('declaration_authority',None)
    return [models[k] for k in sorted(models)]

def structural_gaps(process_models):
    """Convert missing internal stages into explicit known-unknown boundaries."""
    gaps=[]
    for pm in process_models:
        n=pm.get('expected_stages')
        if not n or n < 2: continue
        by={s['stage']:s for s in pm.get('known_steps',[])}
        for stage in range(2,n):
            if stage in by: continue
            left=by.get(stage-1);right=by.get(stage+1)
            if not (left and right): continue
            ev=[x for x in [pm.get('declaration_id'),left.get('evidence_id'),right.get('evidence_id')] if x]
            gaps.append({
                'process':pm['process'], 'missing_stage':stage,
                'from_symbol':left['to_symbol'], 'to_symbol':right['from_symbol'],
                'evidence_ids':ev, 'confidence':0.95,
                'reason':f"{pm['process']} declares {n} ordered stages; stage {stage} is absent between supported stages {stage-1} and {stage+1}."
            })
    return gaps

def _normalize_gap(g, known_ids):
    if not isinstance(g,dict): return None
    fr=str(g.get('from_symbol','')).upper().strip()
    to=str(g.get('to_symbol','')).upper().strip()
    pr=str(g.get('process','')).upper().strip()
    ids=[str(x) for x in g.get('evidence_ids',[]) if str(x) in known_ids]
    try: conf=float(g.get('confidence',0.0))
    except Exception: conf=0.0
    if not (OPAQUE_RE.fullmatch(fr or '') and OPAQUE_RE.fullmatch(to or '')): return None
    return {'process':pr,'from_symbol':fr,'to_symbol':to,'evidence_ids':ids,'confidence':max(0.0,min(1.0,conf))}

def build_gap_state(model, world, archive):
    """First idle phase: replay, build a process graph, and expose structural gaps.

    No future question and no candidate learning document is used here. `model` is
    accepted for API compatibility but is intentionally not called.
    """
    groups=select_replay_groups(archive)
    selected=[];seen=set()
    for g in groups:
        for o in g:
            if o['id'] not in seen:
                selected.append(dict(o));seen.add(o['id'])
    process_models=build_process_models(selected)
    gaps=structural_gaps(process_models)
    raw=json.dumps({'process_models':process_models,'unresolved_gaps':gaps},indent=2)
    return {
        'selected_memories':selected,
        'groups':[[o['id'] for o in g] for g in groups],
        'process_models':process_models,
        'derived_relations':[],
        'unresolved_gaps':gaps,
        'raw_gap_state':raw,
        'gap_detection_mode':'deterministic_structural_graph'
    }

def gap_detection(world,state):
    got={(g.get('from_symbol'),g.get('to_symbol')) for g in state.get('unresolved_gaps',[])}
    details={};vals=[]
    for q in world['questions']:
        ok=(q['gap_from'],q['gap_to']) in got
        details[q['id']]={'expected':[q['gap_from'],q['gap_to']],'detected':ok}
        vals.append(1.0 if ok else 0.0)
    return (sum(vals)/len(vals) if vals else 0.0),details

def candidate_text(doc): return observation_text(doc)

def eligible_gaps(state,min_confidence=0.5):
    return [g for g in state.get('unresolved_gaps',[]) if float(g.get('confidence',0.0)) >= float(min_confidence)]

def select_gap_curiosity(world,state,candidates,budget=3,min_confidence=0.5):
    """Pursuit is resource-gated: detecting a gap does not imply spending resources on it."""
    gaps=eligible_gaps(state,min_confidence)
    # prioritize confident gaps, then those with more evidence provenance
    gaps=sorted(gaps,key=lambda g:(float(g.get('confidence',0.0)),len(g.get('evidence_ids',[]))),reverse=True)
    chosen=[];seen=set()
    for g in gaps:
        if len(chosen)>=budget: break
        target={g.get('from_symbol'),g.get('to_symbol'),g.get('process')}
        scored=[]
        for d in candidates:
            toks=opaque_tokens(d.get('text',''))
            overlap=len({x for x in target if x} & toks)
            # both boundary symbols is much stronger than one-symbol overlap
            boundary_bonus=20 if g.get('from_symbol') in toks and g.get('to_symbol') in toks else 0
            score=10*overlap + boundary_bonus + AUTHORITY.get(d.get('source','field_note'),2)
            scored.append((score,d['id'],d))
        scored.sort(key=lambda x:(x[0],x[1]), reverse=True)
        if scored:
            d=scored[0][2]
            if d['id'] not in seen: chosen.append(dict(d));seen.add(d['id'])
    return chosen

def select_random(world,candidates,seed,k=3):
    rnd=random.Random(int(world.get('world_seed',1))*1009+seed*17+31)
    arr=[dict(x) for x in candidates];rnd.shuffle(arr);return arr[:k]

def select_generic(model,world,state,candidates,k=3):
    mem='\n'.join(observation_text(o) for o in state.get('selected_memories',[]))
    docs='\n'.join(candidate_text(d) for d in candidates)
    prompt=f"""INVENTED WORLD: {world['name']}

CURRENT PARTIAL MEMORIES:
{mem}

AVAILABLE LEARNING DOCUMENTS:
{docs}

No future task question is available. Choose at most {k} documents that would be most useful for improving the coherence and completeness of the current world model. Do not assume outside knowledge. Prefer authoritative documents over rumors when both address the same issue.

Return strict JSON: {{"document_ids":["c01","c02"]}}"""
    raw=model.chat(SYSTEM,prompt,max_tokens=180)
    data=parse_json(raw,{}) or {};ids=[];known={d['id']:d for d in candidates}
    for x in data.get('document_ids',[]) if isinstance(data.get('document_ids',[]),list) else []:
        x=str(x)
        if x in known and x not in ids: ids.append(x)
    return [dict(known[x]) for x in ids[:k]],raw

def build_post_learning_state(model,world,state,selected_docs):
    """Second idle phase using additive, deterministic graph composition.

    Newly acquired facts are appended to the stored graph. Original observations
    are never rewritten. A bridge is created only when every declared stage is
    explicitly supported after authority resolution. `model` is intentionally not
    called so a perfect acquired fact cannot be lost through generative rewriting.
    """
    base=[dict(x) for x in state.get('selected_memories',[])]
    docs=[dict(x) for x in selected_docs]
    process_models=build_process_models(base+docs)
    gaps_before={(g.get('process'),g.get('missing_stage'),g.get('from_symbol'),g.get('to_symbol')):g for g in state.get('unresolved_gaps',[])}
    unresolved_after=structural_gaps(process_models)
    unresolved_keys={(g.get('process'),g.get('missing_stage'),g.get('from_symbol'),g.get('to_symbol')) for g in unresolved_after}
    resolved=[];derived=[]
    for key,g in gaps_before.items():
        if key not in unresolved_keys:
            # find the stage fact that closed this exact gap
            doc_id=None
            for d in docs:
                tr=parse_transition(d)
                if tr and tr['process']==g.get('process') and tr['stage']==g.get('missing_stage') and tr['from_symbol']==g.get('from_symbol') and tr['to_symbol']==g.get('to_symbol'):
                    doc_id=d['id'];break
            if doc_id:
                resolved.append({'process':g['process'],'missing_stage':g['missing_stage'],'from_symbol':g['from_symbol'],'to_symbol':g['to_symbol'],'document_id':doc_id})

    for pm in process_models:
        n=pm.get('expected_stages');steps={s['stage']:s for s in pm.get('known_steps',[])}
        if not n or any(i not in steps for i in range(1,n+1)): continue
        ordered=[steps[i] for i in range(1,n+1)]
        if any(ordered[i]['to_symbol'] != ordered[i+1]['from_symbol'] for i in range(len(ordered)-1)): continue
        start_symbol=ordered[0]['from_symbol'];terminal=ordered[-1]['to_symbol']
        evidence_ids=[]
        if pm.get('declaration_id'): evidence_ids.append(pm['declaration_id'])
        evidence_ids += [x['evidence_id'] for x in ordered]
        evidence_ids=list(dict.fromkeys(evidence_ids))
        claim=f"In {pm['process']}, starting from {start_symbol} ultimately reaches {terminal}."
        derived.append({'id':f"dr{len(derived)+1:02d}",'process':pm['process'],'from_symbol':start_symbol,'to_symbol':terminal,'claim':claim,'text':claim,'evidence_ids':evidence_ids,'status':'derived','derivation':'deterministic_stage_composition'})

    return {
        'selected_memories':base,
        'selected_documents':docs,
        'process_models':process_models,
        'resolved_gaps':resolved,
        'unresolved_gaps':unresolved_after,
        'derived_relations':derived,
        'raw_post_dream':json.dumps({'resolved_gaps':resolved,'derived_relations':derived,'unresolved_gaps':unresolved_after},indent=2),
        'consolidation_mode':'additive_deterministic_graph'
    }

def selection_metrics(world,selected_docs):
    got={d['id'] for d in selected_docs};correct={q['correct_document_id'] for q in world['questions']}
    recall=len(got & correct)/len(correct) if correct else 0.0
    precision=len(got & correct)/len(got) if got else 0.0
    return recall,precision,sorted(got & correct)

def bridge_coverage(world,state):
    rels=state.get('derived_relations',[]);details={};vals=[];supported=[]
    for q in world['questions']:
        found=False;sup=False
        for r in rels:
            toks=opaque_tokens(r.get('claim',''))
            if q['start_symbol'] in toks and q['expected_symbol'] in toks:
                found=True
                ids=set(r.get('evidence_ids',[]))
                if q['correct_document_id'] in ids and len(ids & set(q['initial_observation_ids']))>=2: sup=True
        vals.append(1.0 if found else 0.0);supported.append(1.0 if sup else 0.0)
        details[q['id']]={'bridge':found,'supported_bridge':sup}
    return (sum(vals)/len(vals) if vals else 0.0),(sum(supported)/len(supported) if supported else 0.0),details

def retrieval_score(query,text): return 10*len(opaque_tokens(query)&opaque_tokens(text))
def retrieve(items,query,k):
    scored=[]
    for i,it in enumerate(items): scored.append((retrieval_score(query,it.get('text') or it.get('claim','')),-i,it))
    scored.sort(key=lambda x:(x[0],x[1]),reverse=True)
    return [x[2] for x in scored if x[0]>0][:k]

def query_sections(world,items,k):
    secs=[];diag={}
    for q in world['questions']:
        hits=retrieve(items,q['question'],k);diag[q['id']]=[x.get('id','?') for x in hits]
        secs.append(f"MEMORY AVAILABLE FOR {q['id']} (budget={k}):\n"+'\n'.join(f"[{x.get('id','?')}] {x.get('text') or x.get('claim','')}" for x in hits))
    return '\n\n'.join(secs),diag

def direct_learned_sections(world,selected_docs):
    """Control: acquired evidence is sufficient even if second consolidation is bypassed."""
    idmap={o['id']:o for o in world['observations']};cmap={d['id']:d for d in selected_docs}
    secs=[];diag={}
    for q in world['questions']:
        items=[idmap[x] for x in q['initial_observation_ids'] if x in idmap]
        if q['correct_document_id'] in cmap: items.append(cmap[q['correct_document_id']])
        diag[q['id']]=[x['id'] for x in items]
        secs.append(f"MEMORY AVAILABLE FOR {q['id']} (direct acquired evidence control):\n"+'\n'.join(observation_text(x) for x in items))
    return '\n\n'.join(secs),diag

def oracle_relevant_sections(world,candidates):
    idmap={o['id']:o for o in world['observations']};cmap={d['id']:d for d in candidates}
    secs=[];diag={}
    for q in world['questions']:
        # exactly the three transition facts + hidden stage-3 document; omit process-description metadata
        ids=[x for x in q['initial_observation_ids'] if x in idmap and 'contains exactly four ordered transitions' not in idmap[x].get('text','')]
        items=[idmap[x] for x in ids]+[cmap[q['correct_document_id']]]
        diag[q['id']]=[x['id'] for x in items]
        secs.append(f"MEMORY AVAILABLE FOR {q['id']} (oracle relevant chain):\n"+'\n'.join(observation_text(x) for x in items))
    return '\n\n'.join(secs),diag

def answer_prompt(world,memory_text):
    qs='\n'.join(f"{q['id']}: {q['question']}" for q in world['questions'])
    return f"""INVENTED WORLD: {world['name']}\n\nQUERY-TIME MEMORY:\n{memory_text}\n\nQUESTIONS:\n{qs}\n\nAnswer only from the supplied invented-world memory. Return the opaque terminal symbol when supported. If unsupported, answer UNKNOWN. Include every question id.\nReturn ONLY strict JSON: {{\"answers\":[{{\"id\":\"q1\",\"answer\":\"AAA-00\"}}]}}"""

def parse_answers(raw,expected_ids):
    data=parse_json(raw,{}) or {};ans={}
    for a in data.get('answers',[]) if isinstance(data.get('answers',[]),list) else []:
        if isinstance(a,dict) and a.get('id') is not None and a.get('answer') is not None: ans[str(a['id'])]=str(a['answer']).upper().strip()
    missing=[x for x in expected_ids if x not in ans]
    return ans,{'parse_ok':not missing,'missing_ids':missing}

def score_answers(world,answers):
    vals=[];details={}
    for q in world['questions']:
        got=answers.get(q['id'],'');exp=q['expected_symbol'];ok=exp in opaque_tokens(got)
        vals.append(1.0 if ok else 0.0);details[q['id']]={'answer':got,'expected':exp,'score':1.0 if ok else 0.0}
    return sum(vals)/len(vals),details

def cache_key(kind,model_name,seed,world_id,distractors):
    return hashlib.sha1(f"v0722|{kind}|{model_name}|{seed}|{world_id}|{distractors}".encode()).hexdigest()[:18]

def load_or_build(cache_dir,key,builder):
    p=Path(cache_dir)/f"{key}.json"
    if p.exists(): return json.loads(p.read_text(encoding='utf-8')),True
    v=builder();p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2),encoding='utf-8');return v,False
