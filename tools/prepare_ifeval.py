"""bench/ifeval.jsonl from the official IFEval prompts (google-research instruction_following_eval/data/input_data.jsonl),
in file order (the order the published shards use: rows[i::5] matches every published ifeval_s*of5 id list).
  python tools/prepare_ifeval.py <input_data.jsonl>"""
import json, sys
rows = [json.loads(l) for l in open(sys.argv[1])]
assert len(rows) == 541
with open("/home/www/workspace/mathedit/bench/ifeval.jsonl", "w") as f:
    for r in rows:
        f.write(json.dumps({"id": f"ifeval_{r['key']}", "kind": "ifeval", "prompt": r["prompt"],
                            "instruction_id_list": r["instruction_id_list"], "kwargs": r["kwargs"]}, ensure_ascii=False) + "\n")
print("ifeval", len(rows))
