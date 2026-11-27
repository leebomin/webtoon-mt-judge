"""Crop each bubble from the three typeset pages, blind them as A/B/C (shuffled per bubble), and build
(1) the human rating sheet results/typeset_sheet.html and (2) blinded crops for the VLM judges.
Usage: python3 src/typeset_sheet.py <open-mantra dir>"""
import json, os, sys, random, base64, io, html
from PIL import Image

OM = sys.argv[1]
T = ["T1", "T2", "T3"]
ev = json.load(open("data/eval_set.json"))
rng = random.Random(1127)
os.makedirs("runs/typeset/crops", exist_ok=True)
TAGS = ["글자 작음", "단어 중간 끊김", "테두리에 붙음/답답함", "줄 나눔 어색", "치우침/빈 공간", "지운 자국"]

def crop_box(b, W, H):
    x, y, w, h = b["box"]
    cw, ch = max(w * 2.6, 200), max(h * 1.9, 170)
    cx, cy = x + w / 2, y + h / 2
    return tuple(int(v) for v in (max(cx - cw / 2, 0), max(cy - ch / 2, 0), min(cx + cw / 2, W), min(cy + ch / 2, H)))

def b64(im):
    buf = io.BytesIO(); im.save(buf, "JPEG", quality=88); return base64.b64encode(buf.getvalue()).decode()

key, judge_items, crops = {}, {}, {}
for page in ev["pages"]:
    pid = f'{page["book"]}-{page["page_index"]:03d}'
    src = Image.open(os.path.join(OM, page["image"])).convert("RGB")
    ims = {t: Image.open(f"data/typeset/{t}/{pid}.jpg") for t in T}
    for b in page["bubbles"]:
        cb = crop_box(b, *src.size)
        order = T[:]; rng.shuffle(order)
        key[b["id"]] = dict(zip("ABC", order))
        crops[b["id"]] = {"orig": src.crop(cb), **{L: ims[t].crop(cb) for L, t in zip("ABC", order)}}
        for L in "ABC":
            path = f"runs/typeset/crops/{b['id']}_{L}.jpg"; crops[b["id"]][L].save(path, quality=90)
        crops[b["id"]]["orig"].save(f"runs/typeset/crops/{b['id']}_orig.jpg", quality=90)
        judge_items[b["id"]] = {"orig": f"runs/typeset/crops/{b['id']}_orig.jpg", **{L: f"runs/typeset/crops/{b['id']}_{L}.jpg" for L in "ABC"}}
json.dump(key, open("runs/typeset/blind_key.json", "w"), indent=1)
json.dump(judge_items, open("runs/typeset/judge_input.json", "w"), indent=1)

def block(bid, sec, n, perm=None):
    c = dict(crops[bid])
    if perm: c.update({L: crops[bid][src] for L, src in perm.items()})  # perm: shown letter -> main letter
    cells = f'<figure class="orig"><img src="data:image/jpeg;base64,{b64(c["orig"])}"><figcaption>원본</figcaption></figure>'
    for L in "ABC":
        name = f"{sec}|{bid}|{L}"
        radios = "".join(f'<label class="r"><input type="radio" name="{name}" value="{v}">{v}</label>' for v in range(1, 6))
        tags = "".join(f'<label class="t"><input type="checkbox" data-tag="{name}" value="{t}">{t}</label>' for t in TAGS)
        cells += (f'<figure class="cand"><img src="data:image/jpeg;base64,{b64(c[L])}"><figcaption><b class="L">{L}</b>'
                  f'<div class="sc">{radios}</div><div class="tg">{tags}</div><input class="note" data-note="{name}" placeholder="근거 (선택)"></figcaption></figure>')
    return f'<section class="bub"><h3>{n}</h3><div class="row">{cells}</div></section>'

ids = [b["id"] for p in ev["pages"] for b in p["bubbles"]]
body = "".join(block(bid, "main", i + 1) for i, bid in enumerate(ids))
rep = random.Random(5).sample(ids, 6)
rr = random.Random(6); rkey, rb = {}, ""
for i, bid in enumerate(rep):  # letters re-shuffled so the repeat is not a memory test
    srcs = list("ABC"); rr.shuffle(srcs); perm = dict(zip("ABC", srcs))
    rkey[bid] = {L: key[bid][m] for L, m in perm.items()}
    rb += block(bid, "repeat", f"추가 {i + 1}", perm)
json.dump(rkey, open("runs/typeset/repeat_key.json", "w"), indent=1)

CSS = """
:root{--ink:#141414;--mute:#8c8c86;--line:#e2e2de}
*{box-sizing:border-box}body{margin:0;font:14px/1.6 'Gothic A1',system-ui,sans-serif;color:var(--ink);background:#fff}
header{position:sticky;top:0;z-index:2;background:#fff;border-bottom:1px solid var(--line);padding:12px 20px;display:flex;gap:16px;align-items:center;flex-wrap:wrap}
header .p{color:var(--mute)}button{font:inherit;border:1px solid var(--ink);background:var(--ink);color:#fff;padding:6px 14px;cursor:pointer}
.guide,.bub{max-width:1240px;margin:0 auto;padding:0 20px}.guide{margin:20px auto 28px;color:#333}.guide li{margin:2px 0}
.bub{border-top:1px solid var(--ink);padding-top:10px;padding-bottom:28px}.bub h3{margin:0 0 8px;font-size:13px}
.row{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:16px;align-items:start}
figure{margin:0}figure img{width:100%;border:1px solid var(--line);display:block}
.orig figcaption{color:var(--mute);font-size:12px;margin-top:4px}
.L{font-size:15px}.cand.done .L{color:#1f32a8}.r{margin-right:10px}.t{display:inline-block;margin-right:8px;color:#555;font-size:12px}
.note{margin-top:4px;font:inherit;font-size:13px;padding:4px 8px;border:1px solid var(--line);width:100%}
@media(max-width:820px){.row{grid-template-columns:repeat(2,minmax(0,1fr))}}
"""
JS = """
const K='typeset-sheet-1';let S={};try{S=JSON.parse(localStorage.getItem(K)||'{}')}catch(e){}
function save(){try{localStorage.setItem(K,JSON.stringify(S))}catch(e){};prog()}
function prog(){const names=new Set([...document.querySelectorAll('input[type=radio]')].map(e=>e.name));
 const n=[...names].filter(x=>S[x]&&S[x].score).length;document.getElementById('prog').textContent=n+' / '+names.size+' 완료';
 document.querySelectorAll('.cand').forEach(c=>{const r=c.querySelector('input[type=radio]');c.classList.toggle('done',!!(S[r.name]&&S[r.name].score))})}
document.querySelectorAll('input[type=radio]').forEach(e=>{if(S[e.name]&&S[e.name].score==e.value)e.checked=true;
 e.addEventListener('change',()=>{S[e.name]=S[e.name]||{tags:[]};S[e.name].score=+e.value;save()})});
document.querySelectorAll('input[data-tag]').forEach(e=>{const n=e.dataset.tag;if(S[n]&&S[n].tags.includes(e.value))e.checked=true;
 e.addEventListener('change',()=>{S[n]=S[n]||{tags:[]};S[n].tags=S[n].tags.filter(t=>t!==e.value);if(e.checked)S[n].tags.push(e.value);save()})});
document.querySelectorAll('input[data-note]').forEach(e=>{const n=e.dataset.note;if(S[n]&&S[n].note)e.value=S[n].note;
 e.addEventListener('input',()=>{S[n]=S[n]||{tags:[]};S[n].note=e.value;save()})});
document.getElementById('dl').onclick=()=>{const b=new Blob([JSON.stringify(S,null,1)],{type:'application/json'});
 const a=document.createElement('a');a.href=URL.createObjectURL(b);a.download='typeset_ratings.json';a.click()};prog();
"""
GUIDE = """<div class="guide"><b>식자 평가 방법</b><ul>
<li>번역 내용이 아니라 <b>글자를 말풍선에 넣은 모양</b>만 봐 주세요. 세 후보 모두 같은 번역문이에요.</li>
<li>맨 왼쪽은 원래 일본어 페이지 조각이고, A·B·C는 서로 다른 방식으로 한국어를 넣은 결과예요. 방식 이름은 가려져 있고 순서도 매번 섞여 있어요.</li>
<li>5 = 그대로 연재해도 될 만큼 읽기 쉽고 자연스러움 · 4 = 사소한 아쉬움 · 3 = 읽히지만 눈에 띄게 어색함 · 2 = 읽기 불편함 · 1 = 못 읽거나 말풍선을 망침</li>
<li>세 후보가 똑같아 보이면 같은 점수를 주면 돼요.</li><li>문제가 있으면 태그를 눌러 주세요. 지운 자국 = 원문을 지운 흔적이 보이는 경우(세 후보 공통일 수 있어요).</li>
<li>점수는 이 브라우저에 자동 저장돼요. 끝나면 위의 <b>결과 내려받기</b>로 typeset_ratings.json을 보내 주세요. 마지막 6개는 일관성 확인용으로 다시 나오는 문항이에요.</li></ul></div>"""
doc = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>만화 식자 평가표</title><link href="https://fonts.googleapis.com/css2?family=Gothic+A1:wght@400;500;700&display=swap" rel="stylesheet"><style>{CSS}</style></head>
<body><header><b>만화 식자 평가표</b><span class="p" id="prog"></span><button id="dl">결과 내려받기</button></header>{GUIDE}{body}{rb}<script>{JS}</script></body></html>"""
open("results/typeset_sheet.html", "w", encoding="utf-8").write(doc)
print("ok", len(key), "bubbles", os.path.getsize("results/typeset_sheet.html") // 1024, "KB")
