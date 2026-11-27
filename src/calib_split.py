"""Anchor/test split for the typesetting calibration study (plan: runs/typeset_calib/PLAN.md)."""
import json, random
ids = sorted(json.load(open("runs/typeset/judge_input.json")))
anchors = sorted(random.Random(7).sample(ids, 8))
raw = json.load(open("results/typeset_ratings.json"))
ex = {b: {L: {"score": raw[f"main|{b}|{L}"]["score"], "tags": raw[f"main|{b}|{L}"].get("tags", [])} for L in "ABC"} for b in anchors}
json.dump({"anchors": anchors, "test": [b for b in ids if b not in anchors], "anchor_ratings": ex},
          open("runs/typeset_calib/split.json", "w"), ensure_ascii=False, indent=1)
print(anchors)
