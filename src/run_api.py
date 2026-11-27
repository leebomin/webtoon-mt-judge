"""Re-run translation / judging through model APIs with the same prompts.
The results in this repo were produced with Claude models in an agent session (see README);
this script is the API path for re-running or adding models (e.g. HyperCLOVA X).

  python src/run_api.py translate --provider anthropic --model claude-sonnet-5-5 --mode page --out runs/translate_S4.json
  python src/run_api.py judge --provider anthropic --model claude-sonnet-5-5 --image --out runs/judge_sonnet_api_image.json

Keys: ANTHROPIC_API_KEY / GEMINI_API_KEY / CLOVA_API_KEY (+ CLOVA_BASE_URL for an OpenAI-compatible endpoint).
"""
import argparse, base64, json, os, re, pathlib

def b64(path): return base64.b64encode(pathlib.Path(path).read_bytes()).decode()

def call(provider, model, prompt, image=None):
    if provider == "anthropic":
        import anthropic
        content = ([{"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": b64(image)}}] if image else []) + [{"type": "text", "text": prompt}]
        r = anthropic.Anthropic().messages.create(model=model, max_tokens=4000, temperature=0, messages=[{"role": "user", "content": content}])
        return r.content[0].text
    if provider == "gemini":
        from google import genai
        from google.genai import types
        parts = ([types.Part.from_bytes(data=pathlib.Path(image).read_bytes(), mime_type="image/jpeg")] if image else []) + [prompt]
        return genai.Client().models.generate_content(model=model, contents=parts, config=types.GenerateContentConfig(temperature=0)).text
    if provider == "clova":  # OpenAI-compatible endpoint
        from openai import OpenAI
        c = OpenAI(api_key=os.environ["CLOVA_API_KEY"], base_url=os.environ["CLOVA_BASE_URL"])
        content = ([{"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + b64(image)}}] if image else []) + [{"type": "text", "text": prompt}]
        return c.chat.completions.create(model=model, temperature=0, messages=[{"role": "user", "content": content}]).choices[0].message.content
    raise ValueError(provider)

def parse(txt): return json.loads(re.search(r"\{.*\}", txt, re.S).group(0))

ap = argparse.ArgumentParser()
ap.add_argument("task", choices=["translate", "judge"]); ap.add_argument("--provider", required=True); ap.add_argument("--model", required=True)
ap.add_argument("--mode", choices=["page", "line"], default="page"); ap.add_argument("--image", action="store_true"); ap.add_argument("--out", required=True)
a = ap.parse_args(); out = {}
if a.task == "translate":
    inp = json.load(open("runs/translate_input.json", encoding="utf-8"))
    tmpl = open(f"prompts/translate_{a.mode}.md", encoding="utf-8").read()
    for page, lines in inp.items():
        if a.mode == "page":
            out[page] = parse(call(a.provider, a.model, tmpl + "\n\n" + json.dumps(lines, ensure_ascii=False), image=page))
        else:
            out[page] = {k: list(parse(call(a.provider, a.model, tmpl + "\n\n" + json.dumps({"1": v}, ensure_ascii=False))).values())[0] for k, v in lines.items()}
else:
    jin = json.load(open("runs/judge_input.json", encoding="utf-8"))
    clause = ("You also see the manga page image; bubbles are outlined in red and numbered (num). Use the image to check who is speaking, to whom, the scene, and the bubble size."
              if a.image else "You do NOT see the page image; judge from the text only.")
    tmpl = open("prompts/judge.md", encoding="utf-8").read().replace("{IMAGE_CLAUSE}", clause)
    for page, bubbles in jin.items():
        out.update(parse(call(a.provider, a.model, tmpl + "\n\n" + json.dumps(bubbles, ensure_ascii=False), image=page if a.image else None)))
json.dump(out, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("wrote", a.out)
