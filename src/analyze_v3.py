"""v3 decomposed judges vs human, compared with v2 (plan: runs/v3_decomposed/PLAN.md)."""
import json, random, itertools
from scipy.stats import spearmanr
key = json.load(open("runs/blind_key.json")); hk = json.load(open("runs/human_key.json"))
raw = json.load(open("results/human_ratings.json"))
H, HT = {}, {}
for n, v in raw.items():
    sec, b, L = n.split("|")
    if sec == "main": s = hk["main:" + b][L]; H.setdefault(b, {})[s] = v["score"]; HT[(b, s)] = v.get("tags", [])
bids = sorted(H)
def pa(J, sm):
    a = t = 0
    for b in sm:
        for s, u in itertools.combinations(sorted(H[b]), 2):
            h = H[b][s] - H[b][u]
            if h == 0: continue
            j = J[b][s] - J[b][u]; t += 1; a += (j * h > 0) + .5 * (j == 0)
    return a / t
def rho(J, sm): return spearmanr([J[b][s] for b in sm for s in H[b]], [H[b][s] for b in sm for s in H[b]]).correlation
def ci(f, J):
    r = random.Random(0); v = sorted(f(J, [r.choice(bids) for _ in bids]) for _ in range(2000)); return round(v[50], 2), round(v[1949], 2)
def paired(fa, Ja, Jb):  # bootstrap CI of (a - b)
    r = random.Random(1); v = []
    for _ in range(2000):
        sm = [r.choice(bids) for _ in bids]; v.append(fa(Ja, sm) - fa(Jb, sm))
    v.sort(); return round(v[50], 3), round(v[1949], 3)
out = {}
for m in ["sonnet", "opus"]:
    v2 = json.load(open(f"runs/judge_{m}_text.json")); J2 = {b: {key[b][L]: v2[b][L]["score"] for L in "ABC"} for b in v2}
    v3 = json.load(open(f"runs/v3_decomposed/judge_{m}_text.json"))
    Jmin = {b: {key[b][L]: min(v3[b][L]["meaning"], v3[b][L]["naturalness"], v3[b][L]["tone"]) for L in "ABC"} for b in v3}
    Jmean = {b: {key[b][L]: round((v3[b][L]["meaning"] + v3[b][L]["naturalness"] + v3[b][L]["tone"]) / 3) for L in "ABC"} for b in v3}
    Jnat = {b: {key[b][L]: v3[b][L]["naturalness"] for L in "ABC"} for b in v3}
    awk = [(b, s) for (b, s), t in HT.items() if "어색함" in t]
    rec = lambda J: round(sum(J[b][s] <= 4 for b, s in awk) / len(awk), 2)
    fives = lambda J: round(sum(J[b][s] == 5 for b in J for s in J[b]) / 120, 2)
    out[m] = {name: dict(spearman=round(rho(J, bids), 3), spearman_ci=ci(rho, J), pairwise=round(pa(J, bids), 3), pairwise_ci=ci(pa, J),
                          share_5=fives(J), awkward_recall=rec(J))
              for name, J in [("v2", J2), ("v3_min", Jmin), ("v3_mean", Jmean), ("v3_naturalness_only", Jnat)]}
    out[m]["delta_v3min_minus_v2"] = dict(spearman=paired(rho, Jmin, J2), pairwise=paired(pa, Jmin, J2))
out["human"] = dict(share_5=round(sum(H[b][s] == 5 for b in H for s in H[b]) / 120, 2), awkward_items=len([1 for t in HT.values() if "어색함" in t]))
json.dump(out, open("results/summary_v3.json", "w"), indent=1, ensure_ascii=False)
print(json.dumps(out, indent=1, ensure_ascii=False))
