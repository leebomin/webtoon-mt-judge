"""Typesetting calibration study (plan: runs/typeset_calib/PLAN.md).
Compares original judges (runs/typeset/judge_*.json) with anchor-calibrated judges (runs/typeset_calib/judge_*.json)
on the same 32 test bubbles. Paired bootstrap over bubbles."""
import json, random, itertools
import numpy as np
from scipy.stats import spearmanr

T = ["T1", "T2", "T3"]
key = json.load(open("runs/typeset/blind_key.json"))
split = json.load(open("runs/typeset_calib/split.json"))
raw = json.load(open("results/typeset_ratings.json"))
H = {}
for n, v in raw.items():
    sec, b, L = n.split("|")
    if sec == "main" and "score" in v: H.setdefault(b, {})[key[b][L]] = v["score"]
test = [b for b in split["test"] if len(H.get(b, {})) == 3]

def load(p):
    j = json.load(open(p)); return {b: {key[b][L]: j[b][L]["score"] for L in "ABC"} for b in j}
def rho(J, sm): return spearmanr([J[b][t] for b in sm for t in T], [H[b][t] for b in sm for t in T]).correlation
def pa(J, sm):
    a = n = 0
    for b in sm:
        for s, u in itertools.combinations(T, 2):
            h = H[b][s] - H[b][u]
            if h == 0: continue
            j = J[b][s] - J[b][u]; n += 1; a += (j * h > 0) + .5 * (j == 0)
    return a / n
def ci(f, n=2000, seed=0):
    r = random.Random(seed); v = sorted(f([r.choice(test) for _ in test]) for _ in range(n))
    return [round(v[int(n * .025)], 3), round(v[int(n * .975)], 3)]

out = {"n_test": len(test), "anchors": split["anchors"], "human_mean": round(np.mean([H[b][t] for b in test for t in T]), 2), "judges": {}}
for m in ["opus", "sonnet"]:
    O, C = load(f"runs/typeset/judge_{m}.json"), load(f"runs/typeset_calib/judge_{m}.json")
    d = {}
    for name, J in [("original", O), ("with_examples", C)]:
        d[name] = dict(spearman=round(rho(J, test), 3), spearman_ci=ci(lambda s: rho(J, s)),
                       pairwise=round(pa(J, test), 3), pairwise_ci=ci(lambda s: pa(J, s)),
                       mean=round(np.mean([J[b][t] for b in test for t in T]), 2))
    d["diff_spearman"] = dict(mean=round(rho(C, test) - rho(O, test), 3), ci=ci(lambda s: rho(C, s) - rho(O, s)))
    d["diff_pairwise"] = dict(mean=round(pa(C, test) - pa(O, test), 3), ci=ci(lambda s: pa(C, s) - pa(O, s)))
    out["judges"][m] = d
json.dump(out, open("results/summary_calib.json", "w"), indent=1, ensure_ascii=False)
print(json.dumps(out, indent=1, ensure_ascii=False))
