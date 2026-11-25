# -*- coding: utf-8 -*-
"""把 簡報原始檔/ 組成一個可直接放上 GitHub Pages 的 index.html。

用法：python build_pages.py
投影片圖片放在 簡報原始檔/assets/<id>.png，對應投影片裡的 /_blob/<id>。
"""
import html
import io
import json
import os
import re

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "簡報原始檔")

deck = json.load(io.open(os.path.join(SRC, "deck.json"), encoding="utf-8"))
order = deck["order"]

slides = []
for sid in order:
    s = io.open(os.path.join(SRC, "slides", sid + ".html"), encoding="utf-8").read()
    s = re.sub(r'(["(])/_blob/([0-9a-f]{32})', r"\1簡報原始檔/assets/\2.png", s)
    slides.append(s.strip())

fonts = "&".join(
    "family=" + f["family"].replace(" ", "+") + ":wght@400;500;700;900"
    for f in deck.get("faces", {}).values()
)

title = html.escape(deck.get("title", "簡報"))

page = f"""<!doctype html>
<html lang="zh-Hant-TW">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?{fonts}&display=swap">
<style>
:root {{ --bg:#dcdddd; --fg:#ffffff; --muted:#dcdddd; --accent:#248dc5; }}
html, body {{ margin:0; height:100%; background:var(--bg); color:var(--fg);
  font-family:'Noto Sans TC', Arial, sans-serif; overflow:hidden; }}
#viewport {{ position:fixed; inset:0 0 48px 0; display:flex; align-items:center; justify-content:center; }}
#stage {{ position:relative; width:1920px; height:1080px; transform-origin:center center;
  overflow:hidden; background:#ffffff; }}
#stage > section {{ position:absolute; inset:0; width:1920px; height:1080px; box-sizing:border-box;
  display:none !important; overflow:hidden; color:#2a2a2a; }}
#stage > section.active {{ display:flex !important; }}
#stage section * {{ margin:0; box-sizing:border-box; }}
#stage section ul {{ padding-left:1.2em; list-style:disc; }}
#stage section table {{ border-collapse:collapse; width:100%; }}
#stage section th, #stage section td {{ padding:14px 20px; border-bottom:1px solid #9fa0a0; vertical-align:top; }}
#stage section img {{ display:block; object-fit:cover; }}
#stage section .crop-frame {{ overflow:hidden; display:block; }}
#stage section aside {{ display:none; }}
#stage section a {{ color:inherit; }}
#bar {{ position:fixed; left:0; right:0; bottom:0; height:48px; display:flex; align-items:center;
  gap:12px; padding:0 16px; font-size:15px; color:var(--muted); background:#2a2a2a; }}
#bar button {{ background:#3d3d3d; color:var(--fg); border:0; border-radius:0; padding:6px 12px;
  font:inherit; cursor:pointer; }}
#bar button:hover {{ background:#248dc5; }}
#count {{ min-width:72px; text-align:center; color:var(--fg); }}
#progress {{ flex:1; height:4px; background:#3d3d3d; border-radius:2px; overflow:hidden; }}
#progress > div {{ height:100%; background:var(--accent); width:0; transition:width .2s; }}
#notes {{ position:fixed; right:16px; bottom:60px; width:min(560px, calc(100% - 32px)); max-height:45vh;
  overflow:auto; background:#2a2a2a; color:var(--fg); border:1px solid #3d3d3d; border-radius:0;
  padding:16px 18px; font-size:15px; line-height:1.7; white-space:pre-wrap; display:none; }}
body.show-notes #notes {{ display:block; }}
body.fs #bar {{ display:none; }}
body.fs #viewport {{ inset:0; }}
body.fs #notes {{ bottom:16px; }}
@media (max-width: 600px) {{ #bar .hide-sm {{ display:none; }} }}
</style>
</head>
<body>
<div id="viewport"><div id="stage">
{chr(10).join(slides)}
</div></div>
<div id="notes"></div>
<div id="bar">
  <button id="prev" aria-label="上一張">←</button>
  <span id="count"></span>
  <button id="next" aria-label="下一張">→</button>
  <div id="progress"><div></div></div>
  <button id="fs" class="hide-sm">全螢幕（F）</button>
</div>
<script>
(function () {{
  var stage = document.getElementById('stage');
  var slides = Array.prototype.slice.call(stage.querySelectorAll(':scope > section'));
  var notes = document.getElementById('notes');
  var count = document.getElementById('count');
  var bar = document.querySelector('#progress > div');
  var i = 0;

  // data-crop="縮放 x% y%"：照簡報編輯器的畫法。外框沿用圖片原本的位置與大小並裁掉超出部分，
  // 圖片本身放大 zoom 倍，以 cover 填滿，位置由 x、y 決定。
  stage.querySelectorAll('img[data-crop]').forEach(function (img) {{
    var m = /^([\\d.]+)\\s+([\\d.]+)%\\s+([\\d.]+)%$/.exec(img.getAttribute('data-crop').trim());
    if (!m || img.style.objectFit === 'contain') return;
    var z = Math.min(50, Math.max(1, +m[1])), x = Math.min(100, Math.max(0, +m[2])) / 100,
        y = Math.min(100, Math.max(0, +m[3])) / 100;
    if (z === 1) {{ img.style.objectFit = 'cover'; img.style.objectPosition = m[2] + '% ' + m[3] + '%'; return; }}
    var frame = document.createElement('div');
    frame.className = 'crop-frame';
    frame.setAttribute('style', img.getAttribute('style'));
    frame.style.position = img.style.position || 'relative';
    img.parentNode.insertBefore(frame, img);
    frame.appendChild(img);
    var pct = function (v) {{ return (v * 100) + '%'; }};
    img.setAttribute('style', 'position:absolute;max-width:none;max-height:none;object-fit:cover;' +
      'width:' + pct(z) + ';height:' + pct(z) + ';left:' + pct(-(z - 1) * x) + ';top:' + pct(-(z - 1) * y) +
      ';object-position:' + pct(x) + ' ' + pct(y));
  }});

  // 外部連結一律開新分頁；投影片只有一個外部連結時，該張的圖片也可點擊開啟同一個網址。
  slides.forEach(function (s) {{
    var links = s.querySelectorAll('a[href^="http"]');
    links.forEach(function (a) {{ a.target = '_blank'; a.rel = 'noopener'; }});
    if (links.length !== 1) return;
    var href = links[0].href;
    s.querySelectorAll('img').forEach(function (img) {{
      img.style.cursor = 'pointer';
      img.title = href;
      img.addEventListener('click', function (e) {{ e.stopPropagation(); window.open(href, '_blank', 'noopener'); }});
    }});
  }});

  function fit() {{
    var vw = window.innerWidth, vh = window.innerHeight - (document.fullscreenElement ? 0 : 48);
    var s = Math.min(vw / 1920, vh / 1080);
    stage.style.transform = 'scale(' + s + ')';
    stage.style.margin = ((1080 * s - 1080) / 2) + 'px ' + ((1920 * s - 1920) / 2) + 'px';
  }}

  function show(n) {{
    i = Math.max(0, Math.min(slides.length - 1, n));
    slides.forEach(function (el, k) {{ el.classList.toggle('active', k === i); }});
    count.textContent = (i + 1) + ' / ' + slides.length;
    bar.style.width = ((i + 1) / slides.length * 100) + '%';
    var a = slides[i].querySelector('aside');
    notes.textContent = a ? a.textContent.trim() : '（這張沒有講稿）';
    if (location.hash !== '#' + (i + 1)) history.replaceState(null, '', '#' + (i + 1));
  }}

  function fromHash() {{
    var n = parseInt((location.hash || '').slice(1), 10);
    show(isNaN(n) ? 0 : n - 1);
  }}

  document.getElementById('prev').onclick = function () {{ show(i - 1); }};
  document.getElementById('next').onclick = function () {{ show(i + 1); }};
  document.getElementById('fs').onclick = function () {{
    if (document.fullscreenElement) document.exitFullscreen(); else document.documentElement.requestFullscreen();
  }};
  document.getElementById('viewport').addEventListener('click', function (e) {{
    if (e.target.closest('a')) return;
    show(e.clientX < window.innerWidth / 3 ? i - 1 : i + 1);
  }});
  document.addEventListener('keydown', function (e) {{
    var k = e.key;
    if (k === 'ArrowRight' || k === 'PageDown' || k === ' ' || k === 'Enter') {{ e.preventDefault(); show(i + 1); }}
    else if (k === 'ArrowLeft' || k === 'PageUp' || k === 'Backspace') {{ e.preventDefault(); show(i - 1); }}
    else if (k === 'Home') show(0);
    else if (k === 'End') show(slides.length - 1);
    else if (k === 'n' || k === 'N') document.body.classList.toggle('show-notes');
    else if (k === 'f' || k === 'F') document.getElementById('fs').onclick();
  }});
  var x0 = null;
  document.addEventListener('touchstart', function (e) {{ x0 = e.touches[0].clientX; }}, {{ passive: true }});
  document.addEventListener('touchend', function (e) {{
    if (x0 === null) return;
    var dx = e.changedTouches[0].clientX - x0;
    if (Math.abs(dx) > 50) show(dx < 0 ? i + 1 : i - 1);
    x0 = null;
  }});
  document.addEventListener('fullscreenchange', function () {{
    document.body.classList.toggle('fs', !!document.fullscreenElement);
    fit();
  }});
  window.addEventListener('resize', fit);
  window.addEventListener('hashchange', fromHash);
  fit();
  fromHash();
}})();
</script>
</body>
</html>
"""

io.open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8", newline="\n").write(page)
missing = [m for m in set(re.findall(r"簡報原始檔/assets/([0-9a-f]{32})\.png", page))
           if not os.path.exists(os.path.join(SRC, "assets", m + ".png"))]
print("index.html written:", len(slides), "slides; missing assets:", missing or "none")
