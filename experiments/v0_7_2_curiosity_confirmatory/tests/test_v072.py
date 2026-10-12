import json
from pathlib import Path
from curiosity_learning.core import select_gap_curiosity, selection_metrics, bridge_coverage, retrieve, eligible_gaps, build_gap_state, build_post_learning_state, build_archive

ROOT=Path(__file__).resolve().parents[1]
def world(n=1): return json.loads((ROOT/'synthetic_curiosity_scenarios'/f'syn{n:02d}.json').read_text())

def test_synthetic_worlds_are_opaque_and_incomplete():
    ws=list((ROOT/'synthetic_curiosity_scenarios').glob('syn*.json'))
    assert len(ws)==12
    w=world(1); assert len(w['questions'])==3; assert len(w['candidate_documents'])>=12
    for q in w['questions']:
        assert q['correct_document_id']
        assert not any(q['gap_from'] in x['text'] and q['gap_to'] in x['text'] for x in w['observations'])

def test_gap_driven_search_finds_official_missing_docs_with_budget():
    w=world(1)
    state={'unresolved_gaps':[{'process':q['process'],'from_symbol':q['gap_from'],'to_symbol':q['gap_to'],'confidence':0.95,'evidence_ids':q['initial_observation_ids'][:2]} for q in w['questions']]}
    sel=select_gap_curiosity(w,state,w['candidate_documents'],budget=3,min_confidence=0.5)
    recall,precision,hits=selection_metrics(w,sel)
    assert recall==1.0 and precision==1.0
    assert set(hits)=={q['correct_document_id'] for q in w['questions']}

def test_resource_gate_can_decline_low_confidence_gap():
    state={'unresolved_gaps':[{'from_symbol':'AAA-01','to_symbol':'BBB-02','confidence':0.2}]}
    assert eligible_gaps(state,0.5)==[]

def test_supported_bridge_requires_correct_doc_provenance():
    w=world(1); q=w['questions'][0]
    state={'derived_relations':[{'claim':f"{q['start_symbol']} ultimately reaches {q['expected_symbol']}",'evidence_ids':[q['initial_observation_ids'][1],q['initial_observation_ids'][2],q['correct_document_id'],q['initial_observation_ids'][3]]}]}
    b,s,_=bridge_coverage({'questions':[q]},state)
    assert b==1.0 and s==1.0

def test_query_retrieval_does_not_pad_with_zero_overlap():
    w=world(1);q=w['questions'][0]
    items=[{'id':'a','text':f"{q['start_symbol']} maps somewhere"},{'id':'b','text':f"unrelated terminal {q['expected_symbol']}"}]
    hits=retrieve(items,q['question'],2)
    assert [x['id'] for x in hits]==['a']


class NeverCallModel:
    model='never-call'
    def chat(self,*args,**kwargs):
        raise AssertionError('deterministic structural stages must not call the LLM')

def test_structural_gap_detection_finds_all_missing_stage3_links_without_questions():
    w=world(1)
    state=build_gap_state(NeverCallModel(),w,build_archive(w,distractors=0))
    got={(g['process'],g['from_symbol'],g['to_symbol']) for g in state['unresolved_gaps']}
    exp={(q['process'],q['gap_from'],q['gap_to']) for q in w['questions']}
    assert got==exp
    assert all(g['confidence']>=0.9 for g in state['unresolved_gaps'])

def test_additive_post_learning_composes_complete_bridges_with_provenance():
    w=world(1)
    state=build_gap_state(NeverCallModel(),w,build_archive(w,distractors=0))
    cmap={d['id']:d for d in w['candidate_documents']}
    selected=[cmap[q['correct_document_id']] for q in w['questions']]
    post=build_post_learning_state(NeverCallModel(),w,state,selected)
    assert len(post['resolved_gaps'])==3
    b,sup,_=bridge_coverage(w,post)
    assert b==1.0 and sup==1.0
    assert len(post['derived_relations'])==3
