#!/usr/bin/env python3
"""Layout lint for the presentation: opens index.html in headless Chrome/Chromium/Edge at several widths, in light
and dark, and reports what a careful reader would see as broken.

Findings (each one fails the check):
  overflow   an element's content is wider or taller than its box (scrollWidth > clientWidth + 1), or the page
             scrolls sideways
  overlap    two text runs, or a text run and an image/chart, intersect without being parent and child;
             inside charts: two labels, or a label and a bar/target line (a label inside its own bar is allowed)
  crowding   two text runs from different blocks on the same line closer than 12 px
  edge       text closer than 8 px to the left or right edge of the viewport
  spill      content that leaves its slide (it would cover the next one)

It saves one screenshot per slide at the first width and theme, and one per slide that has a finding, then exits
non-zero on any finding. Browser: env CHROME, then toolchain.json ("chrome" in cmd/paths, from hw/ or the user
config written by toolchain-setup), then common install paths.

Examples:
  python3 layout_check.py hw/presentation/index.html
  python3 layout_check.py hw/presentation/index.html --widths 1440 390 --themes light --shots none
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

WIDTHS = [1440, 1280, 1024, 768, 390]
HEIGHT = {1440: 900, 1280: 800, 1024: 768, 768: 1024, 390: 844}

LINT_JS = r"""
(function(){
const F=[];const vw=innerWidth;
const slides=[...document.querySelectorAll('.slide')];
const sid=el=>{const s=el.closest('.slide');return s?(s.id||('#'+slides.indexOf(s))):'page'};
const skip=el=>el.closest('#theme,#tip,#__lint,script,style,noscript');
const short=t=>t.replace(/\s+/g,' ').trim().slice(0,48);
// 1. overflow
if(document.documentElement.scrollWidth>vw+1)F.push({kind:'overflow',slide:'page',what:'page scrolls sideways ('+document.documentElement.scrollWidth+' > '+vw+')'});
document.querySelectorAll('body *').forEach(el=>{
  if(!(el instanceof HTMLElement)||skip(el))return;
  const cs=getComputedStyle(el);if(cs.display==='none'||cs.display==='inline'||cs.display==='contents')return;
  if(['auto','scroll'].includes(cs.overflowX))return;
  if(el.scrollWidth>el.clientWidth+1&&el.clientWidth>0)F.push({kind:'overflow',slide:sid(el),what:el.tagName.toLowerCase()+(el.className?'.'+String(el.className).split(' ')[0]:'')+' "'+short(el.textContent)+'" '+el.scrollWidth+'>'+el.clientWidth});
});
// 2. text runs (one rect per line box per text node), images and charts
const runs=[];
const tw=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);
let n;while(n=tw.nextNode()){
  if(!n.textContent.trim())continue;const el=n.parentElement;if(!el||skip(el))continue;
  if(el.closest('svg'))continue;
  const cs=getComputedStyle(el);if(cs.visibility==='hidden'||+cs.opacity===0)continue;
  const r=document.createRange();r.selectNodeContents(n);
  const block=el.closest('p,li,td,th,dt,dd,h1,h2,h3,figcaption,div,span.chip,.tile-v,.tile-l,footer');
  for(const b of r.getClientRects()){if(b.width<1||b.height<1)continue;runs.push({b,node:n,el,block,t:short(n.textContent)})}
}
const gfx=[...document.querySelectorAll('img,svg.chart,svg:not(.chart)')].filter(e=>!skip(e)&&!e.parentElement.closest('svg'));
const ov=(a,b,p)=>Math.min(a.right,b.right)-Math.max(a.left,b.left)>p&&Math.min(a.bottom,b.bottom)-Math.max(a.top,b.top)>p;
for(let i=0;i<runs.length;i++){const a=runs[i];
  if(a.b.left<8||a.b.right>vw-8)F.push({kind:'edge',slide:sid(a.el),what:'"'+a.t+'" at '+Math.round(a.b.left)+'–'+Math.round(a.b.right)});
  for(let j=i+1;j<runs.length;j++){const c=runs[j];if(c.node===a.node)continue;
    if(Math.abs(c.b.top-a.b.top)>200)continue;
    if(ov(a.b,c.b,1)){F.push({kind:'overlap',slide:sid(a.el),what:'"'+a.t+'" × "'+c.t+'"'});continue}
    const vo=Math.min(a.b.bottom,c.b.bottom)-Math.max(a.b.top,c.b.top)>Math.min(a.b.height,c.b.height)*0.5;
    if(vo&&a.block!==c.block&&!a.block.contains(c.block)&&!c.block.contains(a.block)){
      const gap=Math.max(c.b.left-a.b.right,a.b.left-c.b.right);
      if(gap<12)F.push({kind:'crowding',slide:sid(a.el),what:'"'+a.t+'" and "'+c.t+'" '+Math.round(gap)+' px apart'});
    }
  }
  for(const g of gfx){if(g.contains(a.el))continue;const gb=g.getBoundingClientRect();
    if(ov(a.b,gb,1))F.push({kind:'overlap',slide:sid(a.el),what:'"'+a.t+'" over '+g.tagName.toLowerCase()});}
}
for(let i=0;i<gfx.length;i++)for(let j=i+1;j<gfx.length;j++){const a=gfx[i].getBoundingClientRect(),b=gfx[j].getBoundingClientRect();
  if(ov(a,b,1))F.push({kind:'overlap',slide:sid(gfx[i]),what:gfx[i].tagName.toLowerCase()+' × '+gfx[j].tagName.toLowerCase()})}
// 3. inside charts: labels against labels, bars and the target line
document.querySelectorAll('svg.chart').forEach(svg=>{
  const T=[...svg.querySelectorAll('text')].filter(t=>t.textContent.trim()).map(t=>({t,b:t.getBoundingClientRect()}));
  const M=[...svg.querySelectorAll('rect.bar,line.target')].map(m=>({m,b:m.getBoundingClientRect()}));
  for(let i=0;i<T.length;i++){
    for(let j=i+1;j<T.length;j++)if(ov(T[i].b,T[j].b,1))F.push({kind:'overlap',slide:sid(svg),what:'chart "'+short(T[i].t.textContent)+'" × "'+short(T[j].t.textContent)+'"'});
    if(T[i].t.classList.contains('target-label'))continue;
    for(const k of M){const inside=T[i].t.classList.contains('val-in')&&k.m.tagName==='rect'&&T[i].b.left>=k.b.left-1&&T[i].b.right<=k.b.right+1&&T[i].b.top>=k.b.top-2&&T[i].b.bottom<=k.b.bottom+2;
      const thin=k.m.tagName==='line'?{left:k.b.left-1,right:k.b.right+1,top:k.b.top,bottom:k.b.bottom}:k.b;
      if(!inside&&ov(T[i].b,thin,0.5))F.push({kind:'overlap',slide:sid(svg),what:'chart "'+short(T[i].t.textContent)+'" × '+(k.m.tagName==='line'?'target line':'bar')})}
  }
});
// 4. spill: content outside its slide
slides.forEach(s=>{const sb=s.getBoundingClientRect();s.querySelectorAll('.frame *, footer').forEach(el=>{
  if(skip(el))return;const b=el.getBoundingClientRect();if(b.width<1||b.height<1)return;
  if(b.bottom>sb.bottom+1||b.top<sb.top-1)F.push({kind:'spill',slide:s.id,what:el.tagName.toLowerCase()+' "'+short(el.textContent||'')+'" leaves the slide'})})});
// de-duplicate
const seen=new Set();const out=F.filter(f=>{const k=f.kind+f.slide+f.what;if(seen.has(k))return false;seen.add(k);return true});
parent.postMessage({__lint:{vw:innerWidth,vh:innerHeight,slides:slides.map(s=>s.id),findings:out}},'*');
})();
"""


def toolchain_browser(start_dir):
    """argv list for a headless-capable browser, or None"""
    if os.environ.get("CHROME"):
        return [os.environ["CHROME"]]
    base = os.environ.get("APPDATA") if os.name == "nt" else os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
    cands = []
    d = os.path.abspath(start_dir)
    for _ in range(4):                       # hw/toolchain.json next to or above the deck
        cands.append(os.path.join(d, "toolchain.json"))
        cands.append(os.path.join(d, "hw", "toolchain.json"))
        d = os.path.dirname(d)
    cands.append(os.path.join(base or "", "hardware-design-toolkit", "toolchain.json"))
    for p in cands:
        if os.path.isfile(p):
            try:
                tc = json.load(open(p))
            except (OSError, json.JSONDecodeError):
                continue
            cmd = (tc.get("cmd") or {}).get("chrome")
            if cmd:
                return list(cmd)
            path = (tc.get("paths") or {}).get("chrome")
            if path:
                return [path]
    for c in ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
              "/Applications/Chromium.app/Contents/MacOS/Chromium",
              "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
              shutil.which("google-chrome"), shutil.which("google-chrome-stable"), shutil.which("chromium"),
              shutil.which("chromium-browser"), shutil.which("microsoft-edge"), shutil.which("msedge"),
              r"C:\Program Files\Google\Chrome\Application\chrome.exe",
              r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"]:
        if c and os.path.exists(c):
            return [c]
    return None


def headless(browser, args, timeout=120):
    base = ["--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run", "--no-default-browser-check",
            "--disable-background-networking", "--run-all-compositor-stages-before-draw",
            "--virtual-time-budget=4000", "--force-device-scale-factor=1"]
    return subprocess.run(browser + base + args, capture_output=True, text=True, timeout=timeout)


import contextlib
import functools
import http.server
import socketserver
import threading


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass


@contextlib.contextmanager
def serve_directory_loopback(directory):
    """Serve `directory` over an ephemeral 127.0.0.1 HTTP port so headless Chrome never needs --allow-file-access-from-files."""
    handler = functools.partial(_QuietHandler, directory=directory)
    with socketserver.TCPServer(("127.0.0.1", 0), handler) as httpd:
        port = httpd.server_address[1]
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        try:
            yield f"http://127.0.0.1:{port}"
        finally:
            httpd.shutdown()


def _host(path, src, w, h):
    """a page that holds the deck in an iframe of exactly w x h: headless Chrome will not make a window narrower
    than about 500 px, and its window height includes browser chrome, so the iframe is the real viewport"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"""<!doctype html><html><head><meta charset="utf-8"><style>html,body{{margin:0;background:#9a9a9a}}
iframe{{display:block;border:0;width:{w}px;height:{h}px;background:#fff}}</style></head><body>
<iframe src="{src}"></iframe><script>addEventListener('message',e=>{{if(!e.data||!e.data.__lint)return;
const p=document.createElement('pre');p.id='__lint';p.textContent=JSON.stringify(e.data.__lint);document.body.appendChild(p)}})</script>
</body></html>""")


def _window(w, h):
    return f"--window-size={max(w, 500) + 16},{h + 120}"


def lint_once(browser, html_path, width, theme, tmp):
    import html as H
    d = os.path.dirname(os.path.abspath(html_path))
    src = open(html_path, encoding="utf-8").read()
    probe = src.replace("</body>", f"<script>addEventListener('load',()=>setTimeout(()=>{{{LINT_JS}}},80))</script></body>")
    # probe and host sit next to the deck so relative image paths keep working
    pp = os.path.join(d, f".layout-probe-{width}-{theme}.html")
    hp = os.path.join(d, f".layout-host-{width}-{theme}.html")
    h = HEIGHT.get(width, 900)
    with open(pp, "w", encoding="utf-8") as f:
        f.write(probe)
    _host(hp, os.path.basename(pp) + f"?theme={theme}", width, h)
    try:
        with serve_directory_loopback(d) as base_url:
            r = headless(browser, [_window(width, h), "--dump-dom", f"{base_url}/{os.path.basename(hp)}"])
    finally:
        for x in (pp, hp):
            if os.path.exists(x):
                os.remove(x)
    m = re.search(r'<pre id="__lint">(.*?)</pre>', r.stdout, re.S)
    if not m:
        return None
    res = json.loads(H.unescape(m.group(1)))
    if res.get("vw") != width:
        res["findings"].append(dict(kind="error", slide="page", what=f"viewport is {res.get('vw')} px, expected {width}"))
    return res


def shoot(browser, html_path, width, theme, idx, out_png):
    d = os.path.dirname(os.path.abspath(html_path))
    h = HEIGHT.get(width, 900)
    hp = os.path.join(d, f".layout-shot-{width}-{theme}-{idx}.html")
    _host(hp, os.path.basename(html_path) + f"?theme={theme}&slide={idx}", width, h)
    try:
        with serve_directory_loopback(d) as base_url:
            headless(browser, [_window(width, h), f"--screenshot={out_png}", f"{base_url}/{os.path.basename(hp)}"])
    finally:
        os.remove(hp)
    return os.path.exists(out_png)


def run(html_path, widths=WIDTHS, themes=("light", "dark"), out_dir=None, shots="failing", quiet=False):
    browser = toolchain_browser(os.path.dirname(os.path.abspath(html_path)))
    if not browser:
        print("layout_check: no Chrome/Chromium/Edge found (install one, set CHROME, or run toolchain-setup); skipped",
              file=sys.stderr)
        return None
    out_dir = out_dir or os.path.join(os.path.dirname(os.path.abspath(html_path)), "layout-check")
    os.makedirs(out_dir, exist_ok=True)
    total, slides = [], []
    with tempfile.TemporaryDirectory() as tmp:
        for th in themes:
            for w in widths:
                res = lint_once(browser, html_path, w, th, tmp)
                if res is None:
                    total.append(dict(kind="error", slide="page", what=f"lint did not run at {w} px {th}", width=w, theme=th))
                    continue
                slides = res["slides"]
                for f in res["findings"]:
                    f.update(width=w, theme=th)
                    total.append(f)
        if shots != "none" and slides:
            want = set()
            if shots == "all":
                want = {(widths[0], themes[0], i + 1) for i in range(len(slides))}
            for f in total:
                if f["slide"] in slides:
                    want.add((f["width"], f["theme"], slides.index(f["slide"]) + 1))
            for w, th, i in sorted(want):
                shoot(browser, html_path, w, th, i, os.path.join(out_dir, f"{th}-{w}-slide-{i:02d}.png"))
    with open(os.path.join(out_dir, "findings.json"), "w") as f:
        json.dump(total, f, indent=1, ensure_ascii=False)
    if not quiet:
        for f in total:
            print(f"LAYOUT {f['kind']:<9} {f['theme']:<5} {f['width']:>4}px  {f['slide']}: {f['what']}")
    print(f"layout_check: {len(total)} finding(s) across {len(widths)} widths × {len(themes)} themes; screenshots in {out_dir}")
    return total


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("html", help="presentation index.html")
    ap.add_argument("--widths", type=int, nargs="+", default=WIDTHS)
    ap.add_argument("--themes", nargs="+", choices=("light", "dark"), default=["light", "dark"])
    ap.add_argument("--out", help="folder for screenshots and findings.json (default: next to the HTML, layout-check/)")
    ap.add_argument("--shots", choices=("all", "failing", "none"), default="all",
                    help="all: every slide at the first width/theme plus failing ones; failing: only failing ones")
    a = ap.parse_args()
    if not os.path.isfile(a.html):
        print(f"error: {a.html} not found", file=sys.stderr)
        return 1
    res = run(a.html, a.widths, a.themes, a.out, a.shots)
    if res is None:
        return 2
    return 1 if res else 0


if __name__ == "__main__":
    sys.exit(main())
