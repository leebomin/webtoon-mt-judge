"""Blind rating sheet for the human rater (one self-contained HTML file).
Candidate order is shuffled per bubble with a different seed from the judges; system names never appear in the page.
8 bubbles are shown again at the end (re-shuffled) to measure the rater's own consistency."""
import json, os, random, base64, html
SET = os.environ.get("SET", "ja")
RUNS, RES = ("runs", "results") if SET == "ja" else ("runs_en", "results_en")
SYS = ["S1", "S2", "S3"]
es = json.load(open("data/eval_set.json", encoding="utf-8"))
outs = {s: json.load(open(f"{RUNS}/translate_{s}.json", encoding="utf-8")) for s in SYS}
rng = random.Random(1201 if SET == "ja" else 1202)
key, blocks = {}, []
ctx = json.load(open("data/context.json", encoding="utf-8"))
TAGS = ["오역", "누락", "어색함", "말투", "고유명사", "길이"]

def bubble_html(p, k, b, sec):
    order = SYS[:]; rng.shuffle(order)
    key[f"{sec}:{b['id']}"] = dict(zip("ABC", order))
    rows = ""
    for L, s in zip("ABC", order):
        name = f"{sec}|{b['id']}|{L}"
        radios = "".join(f'<label class="r"><input type="radio" name="{name}" value="{v}">{v}</label>' for v in range(1, 6))
        tags = "".join(f'<label class="t"><input type="checkbox" data-tag="{name}" value="{t}">{t}</label>' for t in TAGS)
        rows += f'<div class="cand"><span class="L">{L}</span><p class="ko">{html.escape(outs[s][p["page_file"]][str(k+1)])}</p><div class="sc">{radios}</div><div class="tg">{tags}</div><input class="note" data-note="{name}" placeholder="근거 (선택)"></div>'
    return f'<section class="bub"><h3>{k+1}</h3>{src_html(b)}{rows}</section>'

def src_html(b):
    if SET == "ja":
        return f'<p class="ja">{html.escape(b["ja"])}</p><p class="en">EN · {html.escape(b["en_ref"])}</p>'
    return f'<p class="ja">{html.escape(b["en_ref"])}</p>'

def img(p):
    return base64.b64encode(open(p["page_file"], "rb").read()).decode()

body = ""
for p in es["pages"]:
    bs = "".join(bubble_html(p, k, b, "main") for k, b in enumerate(p["bubbles"]))
    body += f'<div class="page"><img src="data:image/jpeg;base64,{img(p)}"><div class="list"><h2>{p["book"]} · p.{p["page_index"]}</h2><p class="ctx">{html.escape(ctx[p["page_file"]])}</p>{bs}</div></div>'
allb = [(p, k, b) for p in es["pages"] for k, b in enumerate(p["bubbles"]) if len(b["ja"].strip(".…・ ")) > 2]
rep = random.Random(99).sample(allb, 8)
rb = ""
for p, k, b in rep:
    rb += f'<div class="page"><img src="data:image/jpeg;base64,{img(p)}"><div class="list"><h2>추가 문항</h2><p class="ctx">{html.escape(ctx[p["page_file"]])}</p>{bubble_html(p, k, b, "repeat")}</div></div>'
json.dump(key, open(f"{RUNS}/human_key.json", "w"), indent=1)

CSS = """
:root{--ink:#141414;--mute:#8c8c86;--line:#e2e2de;--bg:#fff}
*{box-sizing:border-box}body{margin:0;font:14px/1.6 'Gothic A1',system-ui,sans-serif;color:var(--ink);background:var(--bg)}
header{position:sticky;top:0;z-index:2;background:#fff;border-bottom:1px solid var(--line);padding:12px 20px;display:flex;gap:16px;align-items:center;flex-wrap:wrap}
header b{font-size:15px}header .p{color:var(--mute)}button{font:inherit;border:1px solid var(--ink);background:var(--ink);color:#fff;padding:6px 14px;cursor:pointer}
.guide{max-width:1180px;margin:20px auto;padding:0 20px;color:#333}.guide li{margin:2px 0}
.page{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:28px;max-width:1180px;margin:0 auto 48px;padding:0 20px}
.page img{width:100%;position:sticky;top:64px;border:1px solid var(--line)}
h2{font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:var(--mute);margin:0 0 8px}
.bub{border-top:1px solid var(--ink);padding:10px 0 16px}.bub h3{margin:0;font-size:13px}
.ctx{background:#f3f3f1;padding:10px 12px;margin:0 0 12px;font-size:13px;color:#333}
.ja{margin:2px 0;font-size:15px}.en{margin:0 0 8px;color:var(--mute)}
.cand{display:grid;grid-template-columns:22px 1fr;gap:2px 8px;padding:6px 0;border-top:1px dashed var(--line)}
.L{font-weight:700}.ko{margin:0;font-size:15px}.sc,.tg{grid-column:2}.r{margin-right:12px}.t{margin-right:10px;color:#555;font-size:12px}
.cand.done .L{color:#1f32a8}
.note{grid-column:2;margin-top:4px;font:inherit;font-size:13px;padding:4px 8px;border:1px solid var(--line);width:100%}
@media(max-width:760px){.page{grid-template-columns:1fr}.page img{position:static}}
"""
JS = """
const K='mtjudge2-'+SETNAME;let S={};try{S=JSON.parse(localStorage.getItem(K)||'{}')}catch(e){}
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
 const a=document.createElement('a');a.href=URL.createObjectURL(b);a.download='human_ratings'+(SETNAME=='en'?'_en':'')+'.json';a.click()};prog();
"""
GUIDE = """<div class="guide"><b>평가 방법</b><ul>
<li>말풍선마다 한국어 번역 A·B·C에 1~5점을 매겨 주세요. 어느 모델 번역인지는 가려져 있고, 순서도 말풍선마다 섞여 있어요.</li>
<li>일본어 원문 아래 영어(EN)는 전문 번역가의 공식 번역이에요. 뜻을 확인하는 용도로만 보세요.</li>
<li>5 = 정확하고 자연스러움, 장면과 캐릭터에 맞음 · 4 = 사소한 문제 · 3 = 뜻은 통하지만 어색하거나 일부 틀림 · 2 = 장면을 바꾸는 중요한 오역(화자, 말투 포함) · 1 = 틀림, 누락, 쓸 수 없음</li>
<li><b>인물 관계</b>: 쪽마다 맨 위 회색 상자에 인물, 관계, 원문의 말투(존댓말·반말)를 적어 두었어요. 이 관계에 맞는 말투인지까지 포함해서 평가해 주세요. 관계에 안 맞는 말투면 말투 태그와 함께 감점해요.</li>
<li>해당하는 문제가 있으면 태그도 눌러 주세요. 길이 = 말풍선에 비해 너무 긴 번역.</li>
<li>점수를 깎았다면 아래 칸에 <b>근거</b>를 한 줄 적어 주세요(선택). 모델 판정과 어긋난 사례를 분석할 때 써요.</li>
<li>점수는 이 브라우저에 자동 저장돼요. 다 끝나면 위의 <b>결과 내려받기</b>를 눌러 human_ratings.json을 보내 주세요.</li></ul></div>"""
TITLE = "만화 번역 평가표 · 일→한" if SET == "ja" else "만화 번역 평가표 · 영→한"
if SET == "en":
    GUIDE = GUIDE.replace("<li>일본어 원문 아래 영어(EN)는 전문 번역가의 공식 번역이에요. 뜻을 확인하는 용도로만 보세요.</li>", "<li>이번 세트는 영어 원문(위쪽 문장)을 한국어로 옮긴 번역이에요. 그림은 일본어판이지만 말풍선 번호로 위치만 확인하세요.</li>").replace("human_ratings.json", "human_ratings_en.json")
doc = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{TITLE}</title><link href="https://fonts.googleapis.com/css2?family=Gothic+A1:wght@400;500;700&display=swap" rel="stylesheet"><style>{CSS}</style></head>
<body><header><b>{TITLE}</b><span class="p" id="prog"></span><button id="dl">결과 내려받기</button></header>{GUIDE}{body}{rb}<script>const SETNAME="{SET}";{JS}</script></body></html>"""
open(f"{RES}/rating_sheet.html", "w", encoding="utf-8").write(doc)
print("sheet ok", len(key), "items")
