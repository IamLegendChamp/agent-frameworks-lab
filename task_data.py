import json
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
def load_jsonl(path):
    records = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            records.append(json.loads(line))
    return records

chunks = load_jsonl(DATA_DIR / "policy_chunks.jsonl")
questions = load_jsonl(DATA_DIR / "golden_questions.jsonl")
known_ids = set()
for chunk in chunks:
    known_ids.add(chunk["chunk_id"])

for q in questions:
    for cid in q["expected_chunk_ids"]:
        if cid not in known_ids:
            raise ValueError(f"unknown chunk id {cid} in {q['id']}")
