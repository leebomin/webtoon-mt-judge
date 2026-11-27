"""Judge vs human agreement.
Inputs: runs/blind_key.json, runs/judge_<name>.json (letters), results/human.json (exported from the rating sheet).
Outputs: results/summary.json + printed table."""
import json, os, glob, random, itertools, statistics as st
from scipy.stats import spearmanr, kendalltau
SET = os.environ.get("SET", "ja")
RUNS, RES = ("runs", "results") if SET == "ja" else ("runs_en", "results_en")

key = json.load(open(f"{RUNS}/blind_key.json"))
hkey = json.load(open(f"{RUNS}/human_key.json"))
raw = json.load(open(f"{RES}/human_ratings" + ("" if SET == "ja" else "_en") + ".json"))         # {"main|<bid>|<letter>": {"score": n, "tags": [...]}}
human_raw = {"main": {}, "repeat": {}}
for name, v in raw.items():
    if not v.get("score"): continue
    sec, bid, L = name.split("|")
    human_raw[sec].setdefault(bid, {})[hkey[f"{sec}:{bid}"][L]] = v["score"]
H = human_raw["main"]

def to_sys(j):  # judge letters -> systems
    return {bid: {key[bid][L]: v["score"] for L, v in d.items()} for bid, d in j.items()}

def pairs(a, b):
    xs, ys = [], []
    for bid in a:
        for s in a[bid]:
            if bid in b and s in b[bid]: xs.append(a[bid][s]); ys.append(b[bid][s])
    return xs, ys

def pairwise_acc(a, b):
    """Within a bubble, does the judge order two systems the same way as the human? (human ties skipped)"""
    agree = tot = 0
    for bid in a:
        for s, t in itertools.combinations(sorted(a[bid]), 2):
            h = b[bid][s] - b[bid][t]
            if h == 0: continue
            j = a[bid][s] - a[bid][t]
            tot += 1; agree += (j * h > 0) + 0.5 * (j == 0)
    return agree / tot if tot else float("nan"), tot

def boot(fn, bids, n=2000, seed=0):
    r = random.Random(seed); vals = []
    for _ in range(n):
        smp = [r.choice(bids) for _ in bids]
        vals.append(fn(smp))
    vals.sort(); return vals[int(.025 * n)], vals[int(.975 * n)]

out = {}
bids = sorted(H)
for f in sorted(glob.glob(f"{RUNS}/judge_*.json")):
    name = f.split("judge_")[1][:-5]
    if name == "input": continue
    J = to_sys(json.load(open(f)))
    xs, ys = pairs(J, H)
    rho = spearmanr(xs, ys).correlation; tau = kendalltau(xs, ys).correlation
    pa, n = pairwise_acc(J, H)
    def rho_of(sm):
        a = [J[b][s] for b in sm for s in J[b]]; c = [H[b][s] for b in sm for s in J[b]]
        return spearmanr(a, c).correlation
    def pa_of(sm):
        return pairwise_acc({b: J[b] for b in sm}, {b: H[b] for b in sm})[0]
    sysmean = {s: st.mean(J[b][s] for b in J) for s in ["S1", "S2", "S3"]}
    out[name] = dict(spearman=rho, spearman_ci=boot(rho_of, bids), kendall=tau,
                     pairwise_acc=pa, pairwise_ci=boot(pa_of, bids), pairwise_n=n, system_mean=sysmean)
out["human_system_mean"] = {s: st.mean(H[b][s] for b in H) for s in ["S1", "S2", "S3"]}
R = human_raw.get("repeat", {})
if R:
    xs, ys = pairs(R, H); out["human_repeat_spearman"] = spearmanr(xs, ys).correlation
    out["human_repeat_exact"] = sum(x == y for x, y in zip(xs, ys)) / len(xs)
json.dump(out, open(f"{RES}/summary.json", "w"), indent=1, ensure_ascii=False)
for k, v in out.items(): print(k, v)

# disagreement cases: |judge - human| >= 2, with the rater's note and the judge's tags
notes = {}
for name, v in raw.items():
    sec, bid, L = name.split("|")
    if sec == "main": notes[(bid, hkey[f"main:{bid}"][L])] = (v.get("note", ""), v.get("tags", []))
jin = json.load(open(f"{RUNS}/judge_input.json", encoding="utf-8"))
cand = {}
for page in jin.values():
    for bid, d in page["bubbles"].items():
        for L in "ABC": cand[(bid, key[bid][L])] = (d.get("ja") or d.get("en"), d[L])
rows = []
for f in sorted(glob.glob(f"{RUNS}/judge_*_*.json")):
    jname = f.split("judge_")[1][:-5]; jr = json.load(open(f))
    for bid, d in jr.items():
        for L, v in d.items():
            s = key[bid][L]
            if bid in H and s in H[bid] and abs(v["score"] - H[bid][s]) >= 2:
                rows.append(dict(judge=jname, bubble=bid, system=s, source=cand[(bid, s)][0], ko=cand[(bid, s)][1],
                                 judge_score=v["score"], judge_tags=v.get("tags", []), human_score=H[bid][s],
                                 human_tags=notes.get((bid, s), ("", []))[1], human_note=notes.get((bid, s), ("", []))[0]))
json.dump(rows, open(f"{RES}/disagreements.json", "w"), ensure_ascii=False, indent=1)
print(len(rows), "disagreement rows")
