import json
from pathlib import Path
from synthetic_learning.runner import METHODS, run_one
from synthetic_learning.core import build_archive, build_replay_state, bridge_coverage

ROOT=Path(__file__).resolve().parents[1]

def world1(): return json.loads((ROOT/'synthetic_scenarios'/'syn01.json').read_text())

def test_oracle_method_registered():
    assert 'oracle_relevant' in METHODS

def test_questions_have_four_oracle_ids():
    w=world1(); ids={o['id'] for o in w['observations']}
    for q in w['questions']:
        assert len(q['oracle_observation_ids'])==4
        assert set(q['oracle_observation_ids']) <= ids

def test_oracle_excludes_rumor_fifth_observation():
    w=world1()
    assert w['questions'][0]['oracle_observation_ids']==['o01','o02','o03','o04']
    assert 'o05' not in w['questions'][0]['oracle_observation_ids']

def test_archive_has_distractors():
    w=world1(); a=build_archive(w,10)
    assert len(a)==len(w['observations'])+10

def test_replay_is_query_independent_structure():
    w=world1(); a=build_archive(w,10); s=build_replay_state(w,a)
    assert 'selected_memories' in s and 'groups' in s
