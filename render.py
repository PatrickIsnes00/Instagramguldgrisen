#!/usr/bin/env python3
"""Guldgrisen Instagram-renderare.

Användning:  python3 render.py posts/2026-11-02/spec.json
Skapar post.jpg (1080x1080) och story.jpg (1080x1920) bredvid spec.json.

Layouter: stat, tips, question, compare, myth
Teman:    green, cream, gold, ink
"""
import asyncio, html, json, sys
from pathlib import Path
from playwright.async_api import async_playwright

THEMES = {
    "green": dict(bg="#0F3B2E", fg="#FBF6EA", sub="#D3E2DA", accent="#F2C14E", card="#FBF6EA", cardfg="#10241D", cardsub="#3A4D45", line="rgba(242,193,78,.16)"),
    "cream": dict(bg="#FBF6EA", fg="#10241D", sub="#3A4D45", accent="#0F3B2E", card="#0F3B2E", cardfg="#FBF6EA", cardsub="#D3E2DA", line="rgba(15,59,46,.10)"),
    "gold":  dict(bg="#F2C14E", fg="#10241D", sub="#2F3B30", accent="#0F3B2E", card="#FBF6EA", cardfg="#10241D", cardsub="#3A4D45", line="rgba(15,59,46,.14)"),
    "ink":   dict(bg="#10241D", fg="#FBF6EA", sub="#C9D8D0", accent="#F2C14E", card="#1B3A2F", cardfg="#FBF6EA", cardsub="#C9D8D0", line="rgba(242,193,78,.14)"),
}

PIG = '<svg width="{s}" height="{s}" viewBox="0 0 64 64" fill="none" stroke="{c}" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 30c0-9 8-15 19-15 9 0 15 3.5 18 8l5-1-1 7c1.5 2 2 4 2 6 0 5-3 9-8 11l-1 6h-6l-1-4h-9l-1 4h-6l-1-7c-6-3-10-8-10-15z"/><path d="M26 15l-3-6 7 3"/><path d="M27 21h10"/><circle cx="44" cy="30" r="1.6" fill="{c}"/><path d="M14 32c-4 0-6-2-6-5"/></svg>'
ARROW = '<svg width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="{c}" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/><path d="M13 6l6 6-6 6"/></svg>'

e = lambda s: html.escape(str(s)).replace("\\n", "<br>").replace("\n", "<br>")


def body(spec, story):
    L = spec["layout"]
    k = f'<div class="kicker">{e(spec.get("kicker",""))}</div>' if spec.get("kicker") else ""
    note = f'<div class="note">{e(spec["note"])}</div>' if spec.get("note") else ""
    if L == "stat":
        rows = "".join(f'<div class="row"><span>{e(a)}</span><b>{e(b)}</b></div>' for a, b in spec.get("rows", []))
        return f'''{k}<h2 class="title">{e(spec["title"])}</h2>
<div class="big"><span class="num">{e(spec["number"])}</span><span class="unit">{e(spec.get("unit",""))}</span></div>
<div class="card rows">{rows}</div>{note}'''
    if L == "tips":
        items = "".join(f'<li><span class="n">{i+1}</span><span>{e(t)}</span></li>' for i, t in enumerate(spec["items"]))
        return f'{k}<h2 class="title lg">{e(spec["title"])}</h2><ol class="tips">{items}</ol>{note}'
    if L == "question":
        return f'''{k}<h2 class="q">{e(spec["question"])}</h2><p class="lead">{e(spec.get("sub",""))}</p>
{f'<div class="cta"><span>{e(spec["cta"])}</span></div>' if spec.get("cta") else ""}{note}'''
    if L == "compare":
        def col(c, hi):
            return f'<div class="card col {"hi" if hi else ""}"><span class="cl">{e(c["label"])}</span><b class="cv">{e(c["value"])}</b><span class="cs">{e(c.get("sub",""))}</span></div>'
        hi = spec.get("highlight", "b")
        return f'''{k}<h2 class="title lg">{e(spec["title"])}</h2>
<div class="cmp">{col(spec["a"], hi=="a")}{col(spec["b"], hi=="b")}</div>
<div class="verdict">{e(spec.get("verdict",""))}</div>{note}'''
    if L == "myth":
        return f'''{k}<div class="mf"><span class="tag no">Myt</span><p class="myth">{e(spec["myth"])}</p></div>
<div class="mf"><span class="tag yes">Fakta</span><p class="fact">{e(spec["fact"])}</p></div>{note}'''
    raise SystemExit(f"Okänd layout: {L}")


def page(spec, theme, story):
    t = THEMES[theme]
    W, H = 1080, (1920 if story else 1080)
    pad = "250px 80px 300px" if story else "72px 80px"
    sc = 1.25 if story else 1.0
    px = lambda v: f"{round(v*sc)}px"
    return f'''<!doctype html><html lang="sv"><head><meta charset="utf-8"><style>
*{{box-sizing:border-box}}body{{margin:0}}
.f{{width:{W}px;height:{H}px;padding:{pad};background:{t["bg"]};color:{t["fg"]};font-family:Inter,sans-serif;display:flex;flex-direction:column;gap:{px(30)};position:relative;overflow:hidden}}
.ring{{position:absolute;border-radius:50%;border:2px solid {t["line"]}}}
.d{{font-family:"Inter Display",Inter,sans-serif;font-weight:800}}
.top{{display:flex;align-items:center;gap:14px;font-family:"Inter Display",Inter,sans-serif;font-weight:800;font-size:{px(30)};letter-spacing:-.5px;position:relative}}
.main{{flex:1;display:flex;flex-direction:column;justify-content:center;gap:{px(28)};position:relative}}
.kicker{{align-self:flex-start;padding:10px 20px;border-radius:999px;background:{t["accent"]};color:{t["bg"]};font-weight:600;font-size:{px(21)};letter-spacing:1.5px;text-transform:uppercase}}
.title{{margin:0;font-family:"Inter Display",Inter,sans-serif;font-weight:800;font-size:{px(52)};line-height:1.05;letter-spacing:-1.5px}}
.title.lg{{font-size:{px(72)};letter-spacing:-2.5px}}
.big{{display:flex;align-items:baseline;gap:18px;flex-wrap:wrap}}
.num{{font-family:"Inter Display",Inter,sans-serif;font-weight:800;font-size:{px(170)};line-height:.9;letter-spacing:-6px;color:{t["accent"]}}}
.unit{{font-size:{px(40)};font-weight:600}}
.card{{background:{t["card"]};color:{t["cardfg"]};border-radius:28px;padding:{px(30)} {px(34)}}}
.rows{{display:flex;flex-direction:column;gap:{px(14)}}}
.row{{display:flex;justify-content:space-between;gap:20px;font-size:{px(26)};color:{t["cardsub"]}}}.row b{{color:{t["cardfg"]};font-weight:700}}
.note{{font-size:{px(19)};color:{t["sub"]};opacity:.9}}
.tips{{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:{px(20)}}}
.tips li{{display:flex;gap:22px;align-items:flex-start;font-size:{px(31)};line-height:1.3}}
.n{{flex:none;width:{px(54)};height:{px(54)};border-radius:50%;background:{t["accent"]};color:{t["bg"]};display:flex;align-items:center;justify-content:center;font-weight:800;font-size:{px(26)}}}
.q{{margin:0;font-family:"Inter Display",Inter,sans-serif;font-weight:800;font-size:{px(96)};line-height:1;letter-spacing:-3.5px}}
.lead{{margin:0;font-size:{px(32)};line-height:1.35;color:{t["sub"]}}}
.cta{{align-self:flex-start;padding:18px 30px;border-radius:999px;border:2px solid {t["accent"]};color:{t["accent"]};font-weight:600;font-size:{px(26)}}}
.cmp{{display:grid;grid-template-columns:repeat({1 if story else 2},minmax(0,1fr));gap:22px}}
.col{{display:flex;flex-direction:column;gap:10px}}.col.hi{{outline:6px solid {t["accent"]};outline-offset:-6px}}
.cl{{font-size:{px(24)};color:{t["cardsub"]}}}.cv{{font-family:"Inter Display",Inter,sans-serif;font-size:{px(62)};letter-spacing:-2px}}.cs{{font-size:{px(21)};color:{t["cardsub"]}}}
.verdict{{font-size:{px(30)};font-weight:600;line-height:1.3}}
.mf{{display:flex;flex-direction:column;gap:14px}}
.tag{{align-self:flex-start;padding:8px 18px;border-radius:10px;font-weight:700;font-size:{px(22)};letter-spacing:1px;text-transform:uppercase}}
.tag.no{{background:transparent;border:2px solid {t["sub"]};color:{t["sub"]}}}.tag.yes{{background:{t["accent"]};color:{t["bg"]}}}
.myth{{margin:0;font-size:{px(40)};line-height:1.2;color:{t["sub"]};text-decoration:line-through;text-decoration-thickness:3px}}
.fact{{margin:0;font-family:"Inter Display",Inter,sans-serif;font-weight:800;font-size:{px(56)};line-height:1.08;letter-spacing:-1.5px}}
.foot{{display:flex;align-items:center;justify-content:space-between;font-size:{px(24)};font-weight:600;position:relative}}
.foot span:last-child{{display:inline-flex;align-items:center;gap:10px;color:{t["accent"]}}}
</style></head><body><div class="f">
<div class="ring" style="right:-160px;top:{"60" if story else "-160"}px;width:520px;height:520px"></div>
<div class="ring" style="right:-80px;top:{"140" if story else "-80"}px;width:360px;height:360px"></div>
<div class="top">{PIG.format(s=px(50), c=t["accent"])}Guldgrisen.se</div>
<div class="main">{body(spec, story)}</div>
<div class="foot"><span>{e(spec.get("footer","Räkna själv på guldgrisen.se"))}</span><span>Guldgrisen.se{ARROW.format(s=px(24), c=t["accent"])}</span></div>
</div></body></html>'''


async def main(spec_path):
    p = Path(spec_path).resolve()
    s = json.loads(p.read_text(encoding="utf-8"))
    async with async_playwright() as pw:
        b = await pw.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
        for kind, story in (("post", False), ("story", True)):
            spec = s[kind]
            theme = spec.get("theme", s.get("theme", "green"))
            pg = await b.new_page(viewport={"width": 1080, "height": 1920 if story else 1080})
            await pg.set_content(page(spec, theme, story))
            await pg.wait_for_timeout(300)
            png = p.parent / f"{kind}.png"
            await pg.screenshot(path=str(png))
            from PIL import Image
            Image.open(png).convert("RGB").save(p.parent / f"{kind}.jpg", quality=88, optimize=True, progressive=True)
            png.unlink()
        await b.close()
    print("OK", p.parent)

if __name__ == "__main__":
    asyncio.run(main(sys.argv[1]))
