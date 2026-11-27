"""Merge system outputs and hide which system wrote which candidate.
Writes runs/judge_input.json (A/B/C per bubble) and runs/blind_key.json (letter -> system)."""
import json, os, random
SET = os.environ.get("SET", "ja")
RUNS, RES = ("runs", "results") if SET == "ja" else ("runs_en", "results_en")
SYS = ["S1", "S2", "S3"]
es = json.load(open("data/eval_set.json", encoding="utf-8"))
outs = {s: json.load(open(f"{RUNS}/translate_{s}.json", encoding="utf-8")) for s in SYS}
rng = random.Random(7 if SET == "ja" else 8)
ctx = json.load(open("data/context.json", encoding="utf-8"))
jin, key = {}, {}
for p in es["pages"]:
    page = {}
    for k, b in enumerate(p["bubbles"]):
        order = SYS[:]; rng.shuffle(order)
        key[b["id"]] = dict(zip("ABC", order))
        page[b["id"]] = {"num": k + 1, **({"ja": b["ja"]} if SET == "ja" else {"en": b["en_ref"]}),
                         **{L: outs[s][p["page_file"]][str(k + 1)] for L, s in zip("ABC", order)}}
    jin[p["page_file"]] = {"context": ctx[p["page_file"]], "bubbles": page}
json.dump(jin, open(f"{RUNS}/judge_input.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
json.dump(key, open(f"{RUNS}/blind_key.json", "w", encoding="utf-8"), indent=1)
print(sum(len(v["bubbles"]) for v in jin.values()), "bubbles blinded")
