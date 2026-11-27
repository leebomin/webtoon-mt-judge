"""Typeset Korean translations into manga pages with three strategies, and log automatic layout metrics.

T1 box + break-all : original (vertical JA) text box, line breaks anywhere between syllables
T2 box + 어절       : original text box, line breaks at spaces (어절); a single 어절 is split only if
                      nothing fits at >= 15px
T3 balloon + 어절   : balloon interior found by flood fill, lines fitted to the balloon's width at each row,
                      어절 breaks with balanced line lengths

All three use the same translation (S1, the best system for the human rater), the same erase step and the
same font, so only the layout strategy differs.
Usage: python3 src/typeset.py <open-mantra dir>  -> data/typeset/<T>/<page>.jpg, runs/typeset_metrics.json
"""
import json, sys, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

OM = sys.argv[1]
FONT = "/root/.fonts/GothicA1-Bold.ttf"
MAX_PX, MIN_PX, READABLE = 26, 11, 15  # below READABLE px, splitting one long 어절 beats shrinking further
NO_LINE_START = set(".,!?…~)]」』'\"")
ev = json.load(open("data/eval_set.json"))
tr = json.load(open("runs/translate_S1.json"))
os.makedirs("data/typeset", exist_ok=True)

def font(px): return ImageFont.truetype(FONT, px)

def width(f, s): return f.getlength(s)

def wrap_breakall(text, f, widths):
    lines, cur, i = [], "", 0
    for ch in text:
        w = widths(len(lines))
        if cur and width(f, cur + ch) > w and ch not in NO_LINE_START:
            lines.append(cur.rstrip()); cur = ch.lstrip()
        else: cur += ch
    if cur.strip(): lines.append(cur.strip())
    return lines

def split_long(text, f, widths):
    out = []
    for wd in text.split():
        if width(f, wd) <= widths(0): out.append(wd); continue
        cur = ""
        for ch in wd:
            if cur and width(f, cur + ch) > widths(0) and ch not in NO_LINE_START: out.append(cur); cur = ch
            else: cur += ch
        out.append(cur)
    return " ".join(out)

def wrap_words(text, f, widths, balance=False, hybrid=False):
    words = (split_long(text, f, widths) if hybrid else text).split()
    def greedy(limit_scale):
        lines, cur = [], ""
        for wd in words:
            w = widths(len(lines)) * limit_scale
            t = (cur + " " + wd).strip()
            if cur and width(f, t) > w: lines.append(cur); cur = wd
            else: cur = t
        if cur: lines.append(cur)
        return lines
    best = greedy(1.0)
    if balance and len(best) > 1:  # shrink the limit while the line count stays the same -> evener lines
        s = 1.0
        while s > 0.5:
            s -= 0.04; c = greedy(s)
            if len(c) != len(best): break
            best = c
    return best

def fits(lines, f, widths, max_lines):
    return len(lines) <= max_lines and all(width(f, l) <= widths(i) + 0.5 for i, l in enumerate(lines))

def erase(img, box):
    x, y, w, h = box
    a = np.asarray(img).copy()
    reg = a[y:y + h, x:x + w]
    border = np.concatenate([a[max(y - 3, 0), x:x + w], a[min(y + h + 2, a.shape[0] - 1), x:x + w],
                             a[y:y + h, max(x - 3, 0)], a[y:y + h, min(x + w + 2, a.shape[1] - 1)]])
    fill = np.median(border, axis=0).astype(np.uint8)
    a[y - 2:y + h + 2, x - 2:x + w + 2] = fill
    return Image.fromarray(a), fill

def balloon_mask(img, box):
    """Light connected region around the (erased) text box, capped to 1.8x the box so open balloons don't leak."""
    g = np.asarray(img.convert("L")) > 200
    x, y, w, h = box
    cx, cy = x + w // 2, y + h // 2
    lab, _ = ndimage.label(g)
    m = lab == lab[cy, cx] if g[cy, cx] else np.zeros_like(g)
    cap = np.zeros_like(g)
    ex, ey = int(w * 0.6), int(h * 0.15)
    cap[max(y - ey, 0):y + h + ey, max(x - ex, 0):x + w + ex] = True
    m &= cap
    if m.sum() < w * h: m = np.zeros_like(g); m[y:y + h, x:x + w] = True  # dark background: fall back to box
    m = ndimage.binary_erosion(m, iterations=6)  # keep text off the balloon outline
    return m

def layout_box(text, box, mode):
    x, y, w, h = box
    pad = 2
    for px, hyb in [(p, False) for p in range(MAX_PX, READABLE - 1, -1)] + [(p, True) for p in range(MAX_PX, MIN_PX - 1, -1)]:
        f = font(px); lh = int(px * 1.25)
        widths = lambda i: w - 2 * pad
        lines = wrap_breakall(text, f, widths) if mode == "T1" else wrap_words(text, f, widths, hybrid=hyb)
        if fits(lines, f, widths, max(1, (h - 2 * pad) // lh)):
            top = y + (h - lh * len(lines)) / 2
            return px, lines, [(x + w / 2, top + i * lh) for i in range(len(lines))], False
    f = font(MIN_PX); lh = int(MIN_PX * 1.25)
    lines = wrap_breakall(text, f, lambda i: w) if mode == "T1" else wrap_words(text, f, lambda i: w)
    top = y + (h - lh * len(lines)) / 2
    return MIN_PX, lines, [(x + w / 2, top + i * lh) for i in range(len(lines))], True

def layout_balloon(text, mask, box):
    ys, xs = np.nonzero(mask)
    cy, cx = ys.mean(), xs.mean()
    c0 = int(round(cx))
    def run(r):  # contiguous free run in row r that contains the centre column
        if not mask[r, c0]: return None
        row = mask[r]; lo = c0; hi = c0
        while lo > 0 and row[lo - 1]: lo -= 1
        while hi < len(row) - 1 and row[hi + 1]: hi += 1
        return lo, hi
    def span(r0, r1):  # horizontal span free in every row r0..r1
        r0, r1 = int(max(r0, 0)), int(min(r1, mask.shape[0] - 1))
        rs = [run(r) for r in range(r0, r1 + 1)]
        if not rs or any(r is None for r in rs): return 0, cx
        lo = max(r[0] for r in rs); hi = min(r[1] for r in rs)
        return max(hi - lo, 0), (lo + hi) / 2
    for px, hyb in [(p, False) for p in range(MAX_PX, READABLE - 1, -1)] + [(p, True) for p in range(MAX_PX, MIN_PX - 1, -1)]:
        f = font(px); lh = int(px * 1.25)
        for n in range(1, 12):
            top = cy - lh * n / 2
            sp = [span(top + i * lh, top + (i + 1) * lh) for i in range(n)]
            widths = lambda i, sp=sp: sp[i][0] if i < len(sp) else 0
            lines = wrap_words(text, f, widths, balance=True, hybrid=hyb)
            if len(lines) == n and fits(lines, f, widths, n):
                return px, lines, [(sp[i][1], top + i * lh) for i in range(n)], False
    px, lines, pos, _ = layout_box(text, box, "T2")
    return px, lines, pos, True

def margin(img, px, lines, pos, fill):
    """Smallest gap in px between the text and existing line art (balloon outline, drawing). Small = cramped."""
    m = Image.new("L", img.size, 0); d = ImageDraw.Draw(m); f = font(px)
    for l, (cx, ty) in zip(lines, pos): d.text((cx, ty), l, font=f, fill=255, anchor="ma")
    t = np.asarray(m) > 0
    art = np.abs(np.asarray(img).astype(int) - fill.astype(int)).max(axis=2) > 90
    dist = ndimage.distance_transform_edt(~art)
    return round(float(dist[t].min()), 1) if t.any() else 0.0

def draw(img, px, lines, pos, ink):
    d = ImageDraw.Draw(img); f = font(px)
    for l, (cx, ty) in zip(lines, pos):
        d.text((cx, ty), l, font=f, fill=ink, anchor="ma")

metrics = {}
for page in ev["pages"]:
    pid = f'{page["book"]}-{page["page_index"]:03d}'
    src = Image.open(os.path.join(OM, page["image"])).convert("RGB")
    ko = tr[f"data/pages/{pid}.jpg"]
    for T in ["T1", "T2", "T3"]:
        img = src.copy()
        fills = {}
        for b in page["bubbles"]:
            img, fills[b["id"]] = erase(img, b["box"])
        for k, b in enumerate(page["bubbles"]):
            text = ko[str(k + 1)]
            ink = (255, 255, 255) if fills[b["id"]].mean() < 110 else (0, 0, 0)
            if T == "T3": px, lines, pos, over = layout_balloon(text, balloon_mask(img, b["box"]), b["box"])
            else: px, lines, pos, over = layout_box(text, b["box"], T)
            gap = margin(img, px, lines, pos, fills[b["id"]])
            draw(img, px, lines, pos, ink)
            words = set(text.split())
            midword = sum(1 for i in range(len(lines) - 1) if (lines[i].split() or [""])[-1] not in words or (lines[i + 1].split() or [""])[0] not in words)
            metrics.setdefault(b["id"], {})[T] = dict(font_px=px, lines=len(lines), midword_breaks=midword, overflow=over, margin_px=gap, text=lines)
        os.makedirs(f"data/typeset/{T}", exist_ok=True)
        img.save(f"data/typeset/{T}/{pid}.jpg", quality=92)
json.dump(metrics, open("runs/typeset_metrics.json", "w"), ensure_ascii=False, indent=1)
for T in ["T1", "T2", "T3"]:
    v = [m[T] for m in metrics.values()]
    print(T, "mean px %.1f" % np.mean([x["font_px"] for x in v]), "midword", sum(x["midword_breaks"] > 0 for x in v),
          "overflow", sum(x["overflow"] for x in v), "median margin", np.median([x["margin_px"] for x in v]), "min px", min(x["font_px"] for x in v))
