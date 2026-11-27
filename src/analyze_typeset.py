"""Typesetting study analysis (plan: runs/typeset/PLAN.md).
Human ratings results/typeset_ratings.json vs VLM judges runs/typeset/judge_*.json vs rule metrics runs/typeset_metrics.json."""
import json, random, itertools, os
import numpy as np
from scipy.stats import spearmanr

T = ["T1", "T2", "T3"]
key = json.load(open("runs/typeset/blind_key.json"))
rkey = json.load(open("runs/typeset/repeat_key.json"))
met = json.load(open("runs/typeset_metrics.json"))
raw = json.load(open("results/typeset_ratings.json"))
H, HT, R = {}, {}, {}
for n, v in raw.items():
    if "score" not in v: continue
    sec, b, L = n.split("|")
    if sec == "main": H.setdefault(b, {})[key[b][L]] = v["score"]; HT[(b, key[b][L])] = v.get("tags", [])
    else: R.setdefault(b, {})[rkey[b][L]] = v["score"]
bids = sorted(b for b in H if len(H[b]) == 3)

scorers = {}
for m in ["sonnet", "opus"]:
    p = f"runs/typeset/judge_{m}.json"
    if os.path.exists(p):
        j = json.load(open(p)); scorers[f"VLM {m}"] = {b: {key[b][L]: j[b][L]["score"] for L in "ABC"} for b in j}
scorers["rule font_px"] = {b: {t: met[b][t]["font_px"] for t in T} for b in met}
scorers["rule -midword"] = {b: {t: -met[b][t]["midword_breaks"] for t in T} for b in met}
scorers["rule margin_px"] = {b: {t: met[b][t]["margin_px"] for t in T} for b in met}

def rho(J, sm): return spearmanr([J[b][t] for b in sm for t in T], [H[b][t] for b in sm for t in T]).correlation
def pa(J, sm):
    a = n = 0
    for b in sm:
        for s, u in itertools.combinations(T, 2):
            h = H[b][s] - H[b][u]
            if h == 0: continue
            j = J[b][s] - J[b][u]; n += 1; a += (j * h > 0) + .5 * (j == 0)
    return a / n if n else float("nan")
def boot(f, *a, n=2000, seed=0):
    r = random.Random(seed); v = sorted(f(*a, [r.choice(bids) for _ in bids]) for _ in range(n))
    return round(v[int(n * .025)], 3), round(v[int(n * .975)], 3)

out = {"n_bubbles": len(bids)}
out["method_mean"] = {t: round(np.mean([H[b][t] for b in bids]), 2) for t in T}
out["method_share_ge4"] = {t: round(np.mean([H[b][t] >= 4 for b in bids]), 2) for t in T}
diff = lambda a, c, sm: np.mean([H[b][a] - H[b][c] for b in sm])
out["method_diff"] = {f"{a}-{c}": dict(mean=round(diff(a, c, bids), 2), ci=boot(diff, a, c)) for a, c in [("T3", "T1"), ("T3", "T2"), ("T2", "T1")]}
out["agreement"] = {}
for name, J in scorers.items():
    out["agreement"][name] = dict(spearman=round(rho(J, bids), 3), spearman_ci=boot(rho, J), pairwise=round(pa(J, bids), 3), pairwise_ci=boot(pa, J))
    if name.startswith("VLM"): out["agreement"][name]["method_mean"] = {t: round(np.mean([J[b][t] for b in bids]), 2) for t in T}
pairs = sum(1 for b in bids for s, u in itertools.combinations(T, 2) if H[b][s] != H[b][u])
out["pairs_non_tied"] = pairs
rb = [b for b in R if len(R[b]) == 3 and b in H]
if rb:
    x = [H[b][t] for b in rb for t in T]; y = [R[b][t] for b in rb for t in T]
    out["human_repeat"] = dict(n=len(rb), spearman=round(spearmanr(x, y).correlation, 3), exact=round(np.mean(np.array(x) == np.array(y)), 2))
def tagstat(tag, f):
    yes = [f(b, t) for (b, t), tg in HT.items() if tag in tg and b in bids]; no = [f(b, t) for (b, t), tg in HT.items() if tag not in tg and b in bids]
    return dict(n_tagged=len(yes), tagged_mean=round(np.mean(yes), 2) if yes else None, untagged_mean=round(np.mean(no), 2) if no else None)
out["tags_vs_rules"] = {
    "단어 중간 끊김 ~ midword_breaks": tagstat("단어 중간 끊김", lambda b, t: met[b][t]["midword_breaks"]),
    "글자 작음 ~ font_px": tagstat("글자 작음", lambda b, t: met[b][t]["font_px"]),
    "테두리에 붙음/답답함 ~ margin_px": tagstat("테두리에 붙음/답답함", lambda b, t: met[b][t]["margin_px"])}
out["tag_counts"] = {t: {tag: sum(tag in HT[(b, t)] for b in bids) for tag in ["글자 작음", "단어 중간 끊김", "테두리에 붙음/답답함", "줄 나눔 어색", "치우침/빈 공간", "지운 자국"]} for t in T}
json.dump(out, open("results/summary_typeset.json", "w"), indent=1, ensure_ascii=False)
print(json.dumps(out, indent=1, ensure_ascii=False))
