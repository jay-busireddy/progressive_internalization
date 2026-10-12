import hashlib, json, math, re
from collections import Counter, defaultdict, deque
from pathlib import Path

SYSTEM = """You are learning an invented world. Every opaque token and rule has NO meaning except what supplied observations establish. Never use outside knowledge or real-world analogies. Respect authority and explicit revisions. Derived relations must be logically supported by the supplied memories."""
AUTHORITY={"rumor":1,"poster":1,"casual_note":2,"field_note":2,"lesson":4,"official_manual":5,"official_revision":6}
STOP=set("a an the and or if then when while into from to of is are was were be becomes become causes cause emits emit changes change transforms transform produces produce after before through with by in on at state object item code output terminal result final eventually ultimately what which does do can will".split())
OPAQUE_RE=re.compile(r'\b[A-Z]{3}-\d{2}\b')

def words(text): return re.findall(r"[a-z0-9_-]+",str(text).lower())
def opaque_tokens(text): return set(OPAQUE_RE.findall(str(text).upper()))
def approx_tokens(text): return max(1,len(str(text).split()))
def observation_text(o):
    return f"[{o['id']}] source={o.get('source','field_note')} authority={AUTHORITY.get(o.get('source','field_note'),2)} :: {o.get('text','')}"

def _distractor(i, world_seed):
    # isolated two-token facts; intentionally do not connect into components of >=3 observations
    a=(world_seed*37+i*7)%90+10; b=(world_seed*53+i*11)%90+10
    p=f"D{world_seed%9}{i%10}X-{a:02d}"[:6]+f"-{a:02d}" if False else f"ZED-{a:02d}"
    q=f"WEX-{b:02d}"
    # duplicate token names are possible across many distractors, so add unique synthetic words as additional anchors
    return {"id":f"d{i:03d}","source":"field_note","text":f"Archive fragment {i}: {p} is catalogued beside {q}; no transformation relation is stated."}

def build_archive(world,distractors=80):
    obs=[dict(x) for x in world['observations']]
    seed=int(world.get('world_seed',1))
    # Create truly isolated distractors using opaque alpha-number-like names that do not match target QXX tokens.
    for i in range(distractors):
        aa=f"X{seed:02d}{i:03d}"; bb=f"Y{seed:02d}{i:03d}"
        obs.append({"id":f"d{i:03d}","source":"field_note","text":f"{aa} is listed adjacent to {bb}; this archival note states no causal or transformation rule."})
    # stable interleave so relevant facts are sparse
    rnd=random_like(seed+distractors)
    rnd.shuffle(obs)
    return obs

def random_like(seed):
    import random
    return random.Random(seed)

def retrieval_score(query,text):
    qo=opaque_tokens(query); to=opaque_tokens(text)
    score=8.0*len(qo & to)
    q=[w for w in words(query) if w not in STOP and len(w)>2]
    t=set(w for w in words(text) if w not in STOP and len(w)>2)
    score += sum(1.0 for w in q if w in t)
    return score

def retrieve(items,query,k):
    scored=[]
    for idx,it in enumerate(items):
        txt=it.get('text') or it.get('claim') or str(it)
        scored.append((retrieval_score(query,txt),-idx,it))
    scored.sort(key=lambda x:(x[0],x[1]), reverse=True)
    return [x[2] for x in scored[:k]]

def _obs_graph(observations):
    # Connect observations only when they share an opaque token. Relevant chains share intermediates;
    # generated distractors have no opaque QXX-style codes and remain isolated.
    toks=[opaque_tokens(o.get('text','')) for o in observations]
    adj=[set() for _ in observations]
    token_to_idx=defaultdict(list)
    for i,ts in enumerate(toks):
        for t in ts: token_to_idx[t].append(i)
    for inds in token_to_idx.values():
        for i in inds:
            for j in inds:
                if i!=j: adj[i].add(j)
    return adj

def select_replay_groups(observations,min_group=3,max_groups=6,max_group_size=8):
    """Query-independent association selector. Returns connected memory neighborhoods.
    It sees only the archive, never questions.
    """
    adj=_obs_graph(observations); seen=set(); groups=[]
    for i in range(len(observations)):
        if i in seen: continue
        stack=[i]; comp=[]; seen.add(i)
        while stack:
            u=stack.pop(); comp.append(u)
            for v in adj[u]:
                if v not in seen: seen.add(v); stack.append(v)
        if len(comp)>=min_group:
            # rank components by authority sum then size, query-independently
            group=[observations[x] for x in comp[:max_group_size]]
            groups.append(group)
    groups.sort(key=lambda g:(sum(AUTHORITY.get(x.get('source','field_note'),2) for x in g),len(g)), reverse=True)
    return groups[:max_groups]

def parse_json(text,default=None):
    try:return json.loads(text)
    except Exception:
        m=re.search(r'\{.*\}',str(text),re.S)
        if m:
            try:return json.loads(m.group(0))
            except Exception:pass
    return default

def build_replay_state(world,archive):
    groups=select_replay_groups(archive)
    selected=[]; seen=set()
    for g in groups:
        for o in g:
            if o['id'] not in seen: selected.append(dict(o));seen.add(o['id'])
    return {'selected_memories':selected,'groups':[[o['id'] for o in g] for g in groups]}

def build_dream_state(model,world,archive):
    replay=build_replay_state(world,archive)
    selected=replay['selected_memories']
    group_text=[]
    idmap={o['id']:o for o in selected}
    for gi,ids in enumerate(replay['groups'],1):
        group_text.append(f"GROUP {gi}:\n"+'\n'.join(observation_text(idmap[i]) for i in ids))
    prompt=f"""INVENTED WORLD: {world['name']}\n\nIDLE REPLAY GROUPS SELECTED BEFORE ANY FUTURE QUERY:\n{chr(10).join(group_text)}\n\nThis is an OFFLINE DREAM/CONSOLIDATION phase. Recombine each connected group and append genuinely NEW multi-step endpoint associations. Do not merely restate one observation. A derived association should connect an upstream opaque symbol to a downstream opaque terminal symbol when the supplied chain logically supports it. Respect official revisions and authority. Every derivation must cite at least 2 source observation IDs. Do not use any future question; none is available.\n\nReturn strict JSON:\n{{"derived_relations":[{{"claim":"...","evidence_ids":["o1","o2"],"confidence":0.0}}]}}"""
    raw=model.chat(SYSTEM,prompt,max_tokens=500)
    data=parse_json(raw,{}) or {}
    known={o['id'] for o in selected}; valid=[]
    for r in data.get('derived_relations',[]) if isinstance(data.get('derived_relations',[]),list) else []:
        if not isinstance(r,dict):continue
        ids=[str(x) for x in r.get('evidence_ids',[]) if str(x) in known]
        claim=str(r.get('claim','')).strip()
        if claim and len(set(ids))>=2:
            valid.append({'id':f"dr{len(valid)+1:02d}",'claim':claim,'text':claim,'evidence_ids':ids,'confidence':r.get('confidence',0.0)})
    return {'selected_memories':selected,'groups':replay['groups'],'derived_relations':valid,'raw_dream':raw}

def cache_key(kind,model_name,seed,scenario_id,distractors):
    return hashlib.sha1(f"v071|{kind}|{model_name}|{seed}|{scenario_id}|{distractors}".encode()).hexdigest()[:18]

def load_or_build_cache(cache_dir,kind,model,world,distractors,builder):
    p=Path(cache_dir)/f"{cache_key(kind,model.model,model.seed,world['id'],distractors)}.json"
    if p.exists():return json.loads(p.read_text(encoding='utf-8')),True
    v=builder();p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2,ensure_ascii=False),encoding='utf-8');return v,False

def _repair_json_container(raw):
    s=str(raw).strip(); starts=[i for i,c in enumerate(s) if c=='{']
    for st in starts:
        cand=s[st:]
        opens=cand.count('{')-cand.count('}'); sq=cand.count('[')-cand.count(']')
        if sq>0:cand+=']'*sq
        if opens>0:cand+='}'*opens
        try:return json.loads(cand)
        except Exception:pass
    return None

def _salvage_answer_objects(raw):
    out=[]
    for m in re.finditer(r'\{\s*"id"\s*:\s*"([^"]+)"\s*,\s*"answer"\s*:\s*"((?:\\.|[^"\\])*)"\s*\}',str(raw),re.S):
        try: ans=json.loads('"'+m.group(2)+'"')
        except Exception: ans=m.group(2)
        out.append({'id':m.group(1),'answer':ans})
    return out

def parse_answer_payload(raw,expected_ids):
    data=None;mode='strict';err=''
    try:data=json.loads(raw)
    except Exception as e:err=f"strict:{type(e).__name__}:{e}"
    if data is None:
        data=_repair_json_container(raw)
        if isinstance(data,dict):mode='repaired_container'
    if data is None:
        s=_salvage_answer_objects(raw)
        if s:data={'answers':s};mode='salvaged_objects'
    if not isinstance(data,dict) or not isinstance(data.get('answers'),list):
        return {'answers':[]},{'parse_ok':False,'parse_mode':'failed','parse_error':err,'missing_ids':list(expected_ids)}
    cleaned=[]
    for a in data['answers']:
        if isinstance(a,dict) and a.get('id') is not None and a.get('answer') is not None:
            cleaned.append({'id':str(a['id']).strip(),'answer':str(a['answer']).strip()})
    got={x['id'] for x in cleaned};missing=[x for x in expected_ids if x not in got]
    return {'answers':cleaned},{'parse_ok':not missing,'parse_mode':mode,'parse_error':err,'missing_ids':missing}

def query_memory_sections(world,items,k):
    sections=[];diag={}
    for q in world['questions']:
        hits=retrieve(items,q['question'],k)
        diag[q['id']]=[h.get('id','?') for h in hits]
        lines=[]
        for h in hits:
            txt=h.get('text') or h.get('claim') or str(h)
            lines.append(f"[{h.get('id','?')}] {txt}")
        sections.append(f"MEMORY AVAILABLE FOR {q['id']} (budget={k}):\n"+'\n'.join(lines))
    return '\n\n'.join(sections),diag

def answer_prompt(world,memory_text):
    qs='\n'.join(f"{q['id']}: {q['question']}" for q in world['questions'])
    return f"""INVENTED WORLD: {world['name']}\n\nQUERY-TIME MEMORY:\n{memory_text}\n\nQUESTIONS:\n{qs}\n\nIf the memory is partitioned into sections named MEMORY AVAILABLE FOR qX, each question must use only its assigned section and must not borrow another question's section. If there are no per-question sections (for example Full History), the whole QUERY-TIME MEMORY applies to every question. Return only compact JSON: {{"answers":[{{"id":"q1","answer":"CODE"}}]}}. Include every question id exactly once. Use opaque symbols exactly. No outside knowledge."""

def call_answer(model,world,memory_text):
    raw=model.chat(SYSTEM,answer_prompt(world,memory_text),max_tokens=260)
    ids=[q['id'] for q in world['questions']];data,meta=parse_answer_payload(raw,ids);return data,raw,meta

def score_answers(world,data,meta=None):
    amap={str(a.get('id')):str(a.get('answer','')) for a in data.get('answers',[]) if isinstance(a,dict)};details=[];scores=[]
    for q in world['questions']:
        ans=amap.get(q['id'],'').upper();exp=q['expected_symbol'].upper();symbols=OPAQUE_RE.findall(ans)
        ok=exp in symbols;bad=any(x.upper() in symbols for x in q.get('forbidden_symbols',[]))
        s=1.0 if ok and not bad else 0.0;scores.append(s);details.append({'id':q['id'],'answer':amap.get(q['id'],''),'expected':exp,'symbols':symbols,'score':s})
    return sum(scores)/max(1,len(scores)),details

def bridge_coverage(world,dream_state):
    rels='\n'.join(r.get('claim','') for r in dream_state.get('derived_relations',[])).upper(); rows=[]
    for q in world['questions']:
        start=q['start_symbol'].upper();end=q['expected_symbol'].upper();ok=(start in rels and end in rels)
        rows.append({'id':q['id'],'start':start,'end':end,'covered':ok})
    return sum(x['covered'] for x in rows)/max(1,len(rows)),rows
