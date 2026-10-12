import json, re, hashlib, random
from collections import defaultdict
from pathlib import Path

SYSTEM = """You are learning an invented synthetic world. Opaque symbols have no meaning except what the supplied observations establish. Never use outside knowledge or real-world analogies. Respect source authority. Do not invent missing transitions. Future task questions are NOT available during idle learning or curiosity."""
AUTHORITY={"rumor":1,"poster":1,"casual_note":2,"field_note":2,"lesson":4,"official_manual":5,"official_revision":6}
OPAQUE_RE=re.compile(r'\b[A-Z]{3}-\d{2}\b')


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
    """First idle consolidation. It must expose incomplete chains without being told the hidden edge."""
    groups=select_replay_groups(archive)
    selected=[];seen=set();group_text=[]
    for gi,g in enumerate(groups,1):
        for o in g:
            if o['id'] not in seen: selected.append(dict(o));seen.add(o['id'])
        group_text.append(f"GROUP {gi}:\n"+'\n'.join(observation_text(o) for o in g))
    prompt=f"""INVENTED WORLD: {world['name']}

IDLE REPLAY GROUPS (selected before any future question):
{chr(10).join(group_text)}

Build a structured model of each process from the supplied memories. A process may explicitly state how many ordered stages it contains. Record every stage that is actually supported by evidence. If two supported fragments leave a specific unresolved transition between them, identify the exact boundary symbols of that missing link. Do not guess the missing rule and do not use a future task question.

For example, if evidence supports AAA-01 -> BBB-02 -> CCC-03 and separately DDD-04 -> EEE-05, and the process description shows these fragments belong to one ordered process, the unresolved boundary is CCC-03 -> DDD-04. This example only illustrates the output format; never reuse its symbols.

Return strict JSON:
{{
  "process_models":[
    {{
      "process":"PRC-00",
      "known_steps":[{{"stage":1,"from_symbol":"AAA-00","to_symbol":"BBB-00","evidence_id":"o1"}}],
      "unresolved_links":[{{"from_symbol":"CCC-00","to_symbol":"DDD-00","evidence_ids":["o1","o2"],"confidence":0.95}}]
    }}
  ],
  "derived_relations":[{{"claim":"...","evidence_ids":["o1","o2"]}}]
}}"""
    raw=model.chat(SYSTEM,prompt,max_tokens=700)
    data=parse_json(raw,{}) or {}
    known={o['id'] for o in selected}
    gaps=[]
    for pm in data.get('process_models',[]) if isinstance(data.get('process_models',[]),list) else []:
        if not isinstance(pm,dict): continue
        process=str(pm.get('process','')).upper().strip()
        for g in pm.get('unresolved_links',[]) if isinstance(pm.get('unresolved_links',[]),list) else []:
            if isinstance(g,dict): g=dict(g);g.setdefault('process',process)
            ng=_normalize_gap(g,known)
            if ng: gaps.append(ng)
    # backwards-compatible parser if the model returns the older shape
    for g in data.get('unresolved_gaps',[]) if isinstance(data.get('unresolved_gaps',[]),list) else []:
        ng=_normalize_gap(g,known)
        if ng: gaps.append(ng)
    uniq=[];seen_gap=set()
    for g in gaps:
        key=(g['process'],g['from_symbol'],g['to_symbol'])
        if key not in seen_gap: uniq.append(g);seen_gap.add(key)
    derived=[]
    for r in data.get('derived_relations',[]) if isinstance(data.get('derived_relations',[]),list) else []:
        if not isinstance(r,dict): continue
        claim=str(r.get('claim','')).strip();ids=[str(x) for x in r.get('evidence_ids',[]) if str(x) in known]
        if claim and len(set(ids))>=2: derived.append({'claim':claim,'text':claim,'evidence_ids':ids})
    return {'selected_memories':selected,'groups':[[o['id'] for o in g] for g in groups], 'derived_relations':derived,'unresolved_gaps':uniq,'raw_gap_state':raw}

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
    """Second idle consolidation. The agent must explicitly revisit its own earlier unresolved gaps."""
    base=[dict(x) for x in state.get('selected_memories',[])]
    all_items=base+[dict(x) for x in selected_docs]
    text='\n'.join(observation_text(o) for o in all_items)
    gap_text='\n'.join(
        f"- process={g.get('process','')} unresolved {g.get('from_symbol','')} -> {g.get('to_symbol','')} confidence={g.get('confidence',0):.2f}"
        for g in state.get('unresolved_gaps',[])
    ) or '(none)'
    prompt=f"""INVENTED WORLD: {world['name']}

PREVIOUSLY DETECTED UNRESOLVED LINKS (created during the first idle consolidation):
{gap_text}

MEMORIES AFTER QUERY-INDEPENDENT LEARNING:
{text}

This is a SECOND IDLE CONSOLIDATION phase. No future task question is available. Revisit the previously unresolved links. When newly acquired evidence explicitly fills one of those links, connect the full process from its supported starting symbol to its supported terminal marker. Do not invent missing transitions. Preserve provenance: cite the original source IDs and the newly acquired document ID that closes the gap.

Return strict JSON:
{{"resolved_gaps":[{{"process":"PRC-00","from_symbol":"CCC-00","to_symbol":"DDD-00","document_id":"c01"}}],"derived_relations":[{{"claim":"Starting from AAA-00 ultimately reaches ZZZ-00.","evidence_ids":["o1","o2","c01","o4"]}}]}}"""
    raw=model.chat(SYSTEM,prompt,max_tokens=650)
    data=parse_json(raw,{}) or {};known={o['id'] for o in all_items};derived=[]
    for r in data.get('derived_relations',[]) if isinstance(data.get('derived_relations',[]),list) else []:
        if not isinstance(r,dict):continue
        claim=str(r.get('claim','')).strip();ids=[str(x) for x in r.get('evidence_ids',[]) if str(x) in known]
        if claim and len(set(ids))>=3:
            derived.append({'id':f"dr{len(derived)+1:02d}",'claim':claim,'text':claim,'evidence_ids':ids})
    return {'selected_memories':base,'selected_documents':[dict(x) for x in selected_docs],'derived_relations':derived,'raw_post_dream':raw}

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
    return hashlib.sha1(f"v0721|{kind}|{model_name}|{seed}|{world_id}|{distractors}".encode()).hexdigest()[:18]

def load_or_build(cache_dir,key,builder):
    p=Path(cache_dir)/f"{key}.json"
    if p.exists(): return json.loads(p.read_text(encoding='utf-8')),True
    v=builder();p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2),encoding='utf-8');return v,False
