#!/usr/bin/env python3
"""Guldgrisen reel-renderare.

Användning:  python3 reel.py reels/2026-11-05/spec.json            -> reel.mp4 (1080x1920, 30 fps)
             python3 reel.py reels/2026-11-05/spec.json --frames 1.5 6 12   -> frame_<t>.jpg att titta på

spec.json:
{
  "theme": "green",                       # green, cream, gold, ink (samma som render.py)
  "scenes": [ {"type": "...", "dur": 3.0, ...}, ... ],
  "caption": "...", "topic": "...", "category": "..."
}

Scentyper (alla tar valfri "dur" i sekunder):
  hook     title (\n = radbrytning), accent (gul rad under), sub
  counter  label, unit_label ("år"), points: [{"x": 1, "in": 6000, "gain": 190}, ...] (räknas i Python),
           value_fmt "kr" – räknar upp siffran och växer staplar (insatt vs avkastning)
  compare  title, a {label, value, sub}, b {label, value, sub}, verdict – korten dyker upp ett i taget
  steps    title, items [..] (3–4 st) – stegen tänds ett i taget
  myth     myth, fact – myten stryks över, sedan kommer fakta
  quiz     question, options [..], answer (index), reveal – svaret markeras efter en paus
  stat     kicker, number, unit, rows [[a,b],..] – siffran räknar upp om den är numerisk
  end      kicker, big, rows [[a,b],..], cta, note – avslutning med uppmaning
"""
import asyncio, json, subprocess, sys
from pathlib import Path
from playwright.async_api import async_playwright

sys.path.insert(0, str(Path(__file__).parent))
from render import THEMES, PIG  # noqa: E402

FPS = 30
BARS = {"green": ("#FBF6EA", "#F2C14E"), "ink": ("#FBF6EA", "#F2C14E"), "cream": ("#0F3B2E", "#F2C14E"), "gold": ("#FBF6EA", "#0F3B2E")}
DEFAULT_DUR = {"hook": 2.6, "counter": 7.5, "compare": 5.5, "steps": 7.0, "myth": 5.5, "quiz": 6.5, "stat": 5.0, "end": 4.5}

HTML = r'''<!doctype html><html lang="sv"><head><meta charset="utf-8"><style>
*{box-sizing:border-box}body{margin:0}
#f{width:1080px;height:1920px;background:BG;color:FG;font-family:Inter,sans-serif;position:relative;overflow:hidden}
.d{font-family:"Inter Display",Inter,sans-serif;font-weight:800}
.ring{position:absolute;border-radius:50%;border:2px solid LINE}
#top{position:absolute;left:90px;top:230px;display:flex;align-items:center;gap:16px;font-size:38px;letter-spacing:-.5px}
/* säker yta för reels: undvik ~250 px upptill, ~380 px nedtill och ~150 px till höger */
.sc{position:absolute;left:90px;right:150px;top:330px;bottom:400px;display:flex;flex-direction:column;justify-content:center;gap:34px;opacity:0}
.acc{color:ACC}.sub{color:SUB}
.h1{margin:0;font-size:138px;line-height:.98;letter-spacing:-5px}
.h2{margin:0;font-size:84px;line-height:1.02;letter-spacing:-3px}
.p{margin:0;font-size:46px;line-height:1.3}
.k{align-self:flex-start;padding:12px 26px;border-radius:999px;background:ACC;color:BG;font-weight:700;font-size:30px;letter-spacing:2px;text-transform:uppercase}
.big{font-size:150px;letter-spacing:-6px;line-height:.95;color:ACC;white-space:nowrap}
.card{background:CARD;color:CARDFG;border-radius:32px;padding:34px 40px}
.rows{display:flex;flex-direction:column;gap:20px;font-size:40px}
.rows div{display:flex;justify-content:space-between;gap:20px}.rows span{color:CARDSUB}.rows b{font-weight:800}
.chart{height:560px;display:flex;align-items:flex-end;gap:6px}
.b{flex:1;display:flex;flex-direction:column-reverse;border-radius:6px 6px 0 0;overflow:hidden}
.b i{display:block;background:BARIN}.b u{display:block;background:BARGAIN}
.legend{display:flex;gap:40px;font-size:32px;color:SUB}.legend span{display:inline-flex;align-items:center;gap:12px}
.legend em{width:26px;height:26px;border-radius:6px;display:inline-block}
.cl{font-size:36px;color:CARDSUB}.cv{font-size:96px;letter-spacing:-3px}.cs{font-size:32px;color:CARDSUB}
.hi{outline:8px solid ACC;outline-offset:-8px}
.step{display:flex;gap:28px;align-items:flex-start;font-size:50px;line-height:1.25}
.n{flex:none;width:76px;height:76px;border-radius:50%;background:ACC;color:BG;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:38px}
.tag{align-self:flex-start;padding:10px 22px;border-radius:12px;font-weight:700;font-size:32px;letter-spacing:1px;text-transform:uppercase}
.tag.no{border:3px solid SUB;color:SUB}.tag.yes{background:ACC;color:BG}
.myth{margin:0;font-size:62px;line-height:1.25;color:SUB;display:inline;background:linear-gradient(ACC,ACC) no-repeat 0 58%/0% 6px;-webkit-box-decoration-break:clone;box-decoration-break:clone}
.fact{margin:0;font-size:80px;line-height:1.05;letter-spacing:-2.5px}
.opt{font-size:52px;padding:30px 38px;border-radius:26px;border:3px solid SUB;display:flex;justify-content:space-between;align-items:center}
.opt.ok{background:ACC;color:BG;border-color:ACC;font-weight:800}
</style></head><body><div id="f">
<div class="ring" style="right:-180px;top:40px;width:600px;height:600px"></div>
<div class="ring" style="right:-90px;top:130px;width:420px;height:420px"></div>
<div id="top" class="d">PIGSVG Guldgrisen.se</div>
<div id="scenes"></div>
</div><script>
const S=SPEC;const esc=s=>String(s??'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/\n/g,'<br>');
const ease=x=>x<0?0:x>1?1:1-Math.pow(1-x,3), io=x=>x<0?0:x>1?1:(x<.5?2*x*x:1-Math.pow(-2*x+2,2)/2);
const fmt=v=>Math.round(v).toLocaleString('sv-SE').replace(/ /g,' ');
const root=document.getElementById('scenes');let t0=0;
const parseNum=s=>{const m=String(s).replace(/\s/g,'').match(/^(-?\d+)$/);return m?parseInt(m[1]):null};
const sc=S.scenes.map(c=>{const el=document.createElement('div');el.className='sc';root.appendChild(el);let h='';
 if(c.type==='hook') h=`<h1 class="h1 d">${esc(c.title)}${c.accent?`<br><span class="acc">${esc(c.accent)}</span>`:''}</h1>${c.sub?`<p class="p sub">${esc(c.sub)}</p>`:''}`;
 if(c.type==='counter') h=`<p class="p sub">${esc(c.label)}</p><div class="h2 d" data-x></div><div class="big d" data-v></div><div class="chart">${c.points.map(()=>'<div class="b"><i></i><u></u></div>').join('')}</div><div class="legend"><span><em style="background:BARIN"></em>${esc(c.in_label||'Det du sätter in')}</span><span><em style="background:BARGAIN"></em>${esc(c.gain_label||'Avkastning')}</span></div>`;
 if(c.type==='compare'){const col=(x,hi)=>`<div class="card ${hi?'hi':''}" data-pop style="display:flex;flex-direction:column;gap:10px"><span class="cl">${esc(x.label)}</span><b class="cv d">${esc(x.value)}</b><span class="cs">${esc(x.sub)}</span></div>`;
   h=`<h2 class="h2 d">${esc(c.title)}</h2>${col(c.a,(c.highlight||'b')==='a')}${col(c.b,(c.highlight||'b')==='b')}<p class="p d" data-pop style="font-size:52px;line-height:1.2">${esc(c.verdict)}</p>`}
 if(c.type==='steps') h=`<h2 class="h2 d">${esc(c.title)}</h2>${c.items.map((it,i)=>`<div class="step" data-pop><span class="n">${i+1}</span><span>${esc(it)}</span></div>`).join('')}`;
 if(c.type==='myth') h=`<span class="tag no">Myt</span><div><p class="myth">${esc(c.myth)}</p></div><span class="tag yes" data-pop>Fakta</span><p class="fact d" data-pop>${esc(c.fact)}</p>`;
 if(c.type==='quiz') h=`<h2 class="h2 d">${esc(c.question)}</h2>${c.options.map((o,i)=>`<div class="opt" data-opt="${i}"><span>${esc(o)}</span><span data-mark></span></div>`).join('')}<p class="p sub" data-pop>${esc(c.reveal)}</p>`;
 if(c.type==='stat') h=`${c.kicker?`<span class="k">${esc(c.kicker)}</span>`:''}${c.title?`<h2 class="h2 d">${esc(c.title)}</h2>`:''}<div class="big d"><span data-num>${esc(c.number)}</span> <span style="font-size:56px;letter-spacing:0;color:FG">${esc(c.unit)}</span></div>${c.rows?`<div class="card rows" data-pop>${c.rows.map(r=>`<div><span>${esc(r[0])}</span><b>${esc(r[1])}</b></div>`).join('')}</div>`:''}`;
 if(c.type==='end') h=`${c.kicker?`<span class="k">${esc(c.kicker)}</span>`:''}${c.big?`<div class="big d">${esc(c.big)}</div>`:''}${c.rows?`<div class="card rows">${c.rows.map(r=>`<div><span>${esc(r[0])}</span><b>${esc(r[1])}</b></div>`).join('')}</div>`:''}<p class="p d" style="font-size:54px;line-height:1.18">${esc(c.cta)}</p>${c.note?`<p class="sub" style="font-size:28px;margin:0">${esc(c.note)}</p>`:''}`;
 el.innerHTML=h;const o={c,el,start:t0,dur:c.dur};t0+=c.dur;
 if(c.type==='myth')o.strike=el.querySelector('.myth');
 if(c.type==='stat')o.num=parseNum(c.number);
 return o});
window.TOTAL=t0;
function pop(el,lt,at){const e=ease((lt-at)/0.45);el.style.opacity=e;el.style.transform=`translateY(${(1-e)*40}px)`}
window.render=function(t){sc.forEach((o,idx)=>{const lt=t-o.start,last=idx===sc.length-1;
  const a=ease(lt/0.45)*(last?1:1-ease((lt-o.dur+0.35)/0.35));
  o.el.style.opacity=(lt<0||lt>o.dur)&&!(last&&lt>o.dur)?0:a;o.el.style.transform=`translateY(${(1-ease(lt/0.45))*60}px)`;
  if(lt<-0.1||(lt>o.dur+0.1&&!last))return;const c=o.c,P=[...o.el.querySelectorAll('[data-pop]')];
  if(c.type==='counter'){const N=c.points.length,p=io((lt-0.3)/(o.dur-1.6)),k=p*N,max=c.points[N-1].in+c.points[N-1].gain;
    const i=Math.min(N-1,Math.max(0,Math.ceil(k)-1)),cur=c.points[i];
    o.el.querySelector('[data-x]').textContent=(k<0.02?0:cur.x)+' '+(c.unit_label||'år');
    o.el.querySelector('[data-v]').textContent=fmt(k<0.02?0:cur.in+cur.gain)+' '+(c.value_fmt||'kr');
    o.el.querySelectorAll('.b').forEach((b,j)=>{const on=j<k;const pt=c.points[j];b.style.height=on?((pt.in+pt.gain)/max*560)+'px':'0';
      b.children[0].style.height=on?(pt.in/max*560)+'px':'0';b.children[1].style.height=on?(pt.gain/max*560)+'px':'0'})}
  if(c.type==='compare'||c.type==='steps'){const gap=(o.dur-1.6)/Math.max(1,P.length);P.forEach((el,j)=>pop(el,lt,0.5+j*gap))}
  if(c.type==='myth'){o.strike.style.backgroundSize=(ease((lt-1.2)/0.5)*100)+'% 6px';P.forEach((el,j)=>pop(el,lt,2.0+j*0.25))}
  if(c.type==='quiz'){const rv=o.dur-2.6;o.el.querySelectorAll('[data-opt]').forEach(el=>{const ok=+el.dataset.opt===c.answer&&lt>rv;el.classList.toggle('ok',ok);el.querySelector('[data-mark]').textContent=ok?'✓':''});P.forEach(el=>pop(el,lt,rv+0.3))}
  if(c.type==='stat'){if(o.num!==null)o.el.querySelector('[data-num]').textContent=fmt(o.num*io((lt-0.2)/1.6));P.forEach(el=>pop(el,lt,1.4))}
 })};
render(0);
</script></body></html>'''


def build_html(spec):
    t = THEMES[spec.get("theme", "green")]
    for s in spec["scenes"]:
        s.setdefault("dur", DEFAULT_DUR[s["type"]])
    h = HTML.replace("BARIN", BARS[spec.get("theme", "green")][0]).replace("BARGAIN", BARS[spec.get("theme", "green")][1])
    for k, v in (("CARDSUB", "cardsub"), ("CARDFG", "cardfg"), ("CARD", "card"), ("LINE", "line"), ("BG", "bg"), ("FG", "fg"), ("SUB", "sub"), ("ACC", "accent")):
        h = h.replace(k, t[v])
    scenes = {"scenes": spec["scenes"]}
    return h.replace("PIGSVG", PIG.format(s="60px", c=t["accent"])).replace("const S=SPEC", "const S=" + json.dumps(scenes, ensure_ascii=False))


async def main(spec_path, frames=None):
    p = Path(spec_path).resolve()
    spec = json.loads(p.read_text(encoding="utf-8"))
    html_path = p.parent / "_reel.html"
    html_path.write_text(build_html(spec), encoding="utf-8")
    async with async_playwright() as pw:
        b = await pw.chromium.launch()
        pg = await b.new_page(viewport={"width": 1080, "height": 1920})
        await pg.goto(html_path.as_uri())
        await pg.wait_for_timeout(400)
        total = await pg.evaluate("TOTAL")
        if frames:
            for t in frames:
                await pg.evaluate(f"render({t})")
                await pg.screenshot(path=str(p.parent / f"frame_{t}.jpg"), type="jpeg", quality=85)
            print(f"Ramar sparade. Total längd {total:.1f} s")
        else:
            tmp = p.parent / "_tmp_reel.mp4"
            ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(FPS), "-c:v", "mjpeg", "-i", "-",
                                   "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-shortest", "-c:v", "libx264", "-crf", "18", "-preset", "veryfast",
                                   "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", str(tmp)], stdin=subprocess.PIPE)
            for i in range(int((total + 0.6) * FPS)):  # +0,6 s paus på slutbilden
                await pg.evaluate(f"render({i / FPS})")
                ff.stdin.write(await pg.screenshot(type="jpeg", quality=92))
            ff.stdin.close()
            if ff.wait() != 0:
                raise SystemExit("ffmpeg misslyckades")
            tmp.rename(p.parent / "reel.mp4")
            print(f"OK {p.parent / 'reel.mp4'} ({total + 0.6:.1f} s)")
        await b.close()
    html_path.unlink()


if __name__ == "__main__":
    a = sys.argv[1:]
    fr = [float(x) for x in a[a.index("--frames") + 1:]] if "--frames" in a else None
    asyncio.run(main(a[0], fr))
