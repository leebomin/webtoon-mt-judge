"""Pick a small, reproducible evaluation set from OpenMantra.

Rule (fixed before looking at any model output):
  - one or two pages per title, pages with 4-6 speech bubbles
  - page order chosen by a fixed random seed
  - stop at 40 bubbles
"""
import json, random, sys, pathlib

OM = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "open-mantra-dataset")
SEED, TARGET = 20261127, 40
books = json.load(open(OM / "annotation.json", encoding="utf-8"))
rng = random.Random(SEED)

cands = {b["book_title"]: [p for p in b["pages"] if 4 <= len(p["text"]) <= 6] for b in books}
for v in cands.values():
    rng.shuffle(v)

picked, n, i = [], 0, 0
titles = sorted(cands)
while n < TARGET:
    t = titles[i % len(titles)]
    j = i // len(titles)
    if j < len(cands[t]):
        p = cands[t][j]
        take = p["text"][: TARGET - n]
        picked.append({"book": t, "page_index": p["page_index"], "image": p["image_paths"]["ja"],
                       "bubbles": [{"id": f"{t}-{p['page_index']:03d}-{k}", "box": [b["x"], b["y"], b["w"], b["h"]],
                                    "ja": b["text_ja"], "en_ref": b["text_en"]} for k, b in enumerate(take)]})
        n += len(take)
    i += 1

json.dump({"seed": SEED, "source": "OpenMantra (CC BY-NC 4.0)", "pages": picked},
          open("data/eval_set.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(len(picked), "pages", n, "bubbles")
for p in picked: print(p["book"], p["page_index"], len(p["bubbles"]))
