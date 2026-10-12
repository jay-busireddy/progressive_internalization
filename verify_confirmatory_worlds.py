from pathlib import Path
import json, hashlib, re, sys

ROOT=Path(__file__).resolve().parent
dream=ROOT/"experiments"/"v0_7_1_dream_confirmatory"/"synthetic_scenarios"
cur=ROOT/"experiments"/"v0_7_2_curiosity_confirmatory"/"synthetic_curiosity_scenarios"

assert len(list(dream.glob("syn*.json")))==12
assert len(list(cur.glob("syn*.json")))==12

opaque=re.compile(r"^[A-Z]{3}-\d{2}$")
for p in dream.glob("syn*.json"):
    w=json.loads(p.read_text())
    assert len(w["questions"])==3 and len(w["observations"])==15
    for q in w["questions"]:
        assert opaque.match(q["start_symbol"]) and opaque.match(q["expected_symbol"])
        assert len(q["oracle_observation_ids"])==4

for p in cur.glob("syn*.json"):
    w=json.loads(p.read_text())
    assert len(w["questions"])==3 and len(w["observations"])==12
    ids={d["id"] for d in w["candidate_documents"]}
    for q in w["questions"]:
        assert q["correct_document_id"] in ids
        assert opaque.match(q["gap_from"]) and opaque.match(q["gap_to"])
        assert len(q["initial_observation_ids"])==4

print("Confirmatory data verification PASSED: 12 Dream worlds + 12 Curiosity worlds.")
