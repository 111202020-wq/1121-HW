"""節點 5：把「已通過忠實度關卡」的逐頁稿機械式轉成 deck/deck.html。

只做排版，不改任何一個字：逐頁稿裡的文字原樣跳脫後放進 HTML。
每頁頁尾的「出處」由該頁引用的證據卡自動對回 wiki 頁名。
用法：py scripts/render_deck.py
"""
import html
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DECK = ROOT / "deck"
sys.stdout.reconfigure(encoding="utf-8")

# 先確認關卡 4 通過，否則不渲染（graph：只能看已通過的逐頁稿）
r = subprocess.run([sys.executable, "-I", str(ROOT / "scripts" / "check_deck.py"), "drafts"],
                   capture_output=True, text=True, encoding="utf-8")
if r.returncode != 0:
    print(r.stdout)
    sys.exit("忠實度關卡未通過，不渲染。請退回逐頁稿。")

sys.path.insert(0, str(ROOT / "scripts"))
from check_deck import load_cards  # noqa: E402

CARDS = load_cards()


def inline(s):
    s = html.escape(s.strip(), quote=False)
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)


def parts(s, sep="|"):
    return [p.strip() for p in s.split(sep)]


CAKE = ('<svg class="cake" viewBox="0 0 24 24" aria-hidden="true"><path d="M4 20h16v-6H4z"/>'
        '<path d="M6 14v-3h12v3"/><path d="M12 11V8"/><path d="M12 5.5c.8.7.8 1.6 0 2-.8-.4-.8-1.3 0-2z"/></svg>')
CHECK = ('<svg class="tick" viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg>')


def bars_svg(spec):
    segs = [p.strip() for p in spec.split(";")]
    title, items = segs[0], [s.split("=") for s in segs[1:]]
    vals = [float(v) for _, v in items]
    W, H, top, base = 300, 230, 34, 196
    vmax = max(vals) * 1.12
    bw, gap = 56, 30
    x0 = (W - (len(items) * bw + (len(items) - 1) * gap)) / 2
    out = [f'<figure class="chart"><figcaption>{inline(title)}</figcaption>'
           f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="{html.escape(title)}">',
           f'<line x1="8" x2="{W - 8}" y1="{base}" y2="{base}" class="axis"/>']
    for i, ((lab, v), val) in enumerate(zip(items, vals)):
        h = (base - top) * val / vmax
        x = x0 + i * (bw + gap)
        cls = "bar last" if i == len(items) - 1 else "bar"
        out.append(f'<rect x="{x:.1f}" y="{base - h:.1f}" width="{bw}" height="{h:.1f}" rx="3" class="{cls}"/>')
        out.append(f'<text x="{x + bw / 2:.1f}" y="{base - h - 8:.1f}" class="val">{html.escape(v)}</text>')
        out.append(f'<text x="{x + bw / 2:.1f}" y="{base + 22}" class="lab">{html.escape(lab)}</text>')
    out.append("</svg></figure>")
    return "".join(out)


def render_blocks(lines):
    out, group, gkind = [], [], None

    def flush():
        nonlocal group, gkind
        if not group:
            return
        if gkind == "kpi":
            out.append('<div class="kpis">' + "".join(
                f'<div class="kpi"><b>{inline(a)}</b><span>{inline(b)}</span></div>' for a, b in group) + "</div>")
        elif gkind == "ul":
            out.append("<ul>" + "".join(f"<li>{inline(x)}</li>" for x in group) + "</ul>")
        elif gkind == "step":
            out.append('<ol class="steps">' + "".join(
                f'<li><b>{inline(a)}</b><span>{inline(b)}</span></li>' for a, b in group) + "</ol>")
        elif gkind == "card":
            cells = []
            for f in group:
                body = f[2]
                cake = body.startswith("蛋糕：")
                body_html = (f'<p class="cakeline">{CAKE}{inline(body[3:])}</p>' if cake
                             else f"<p>{inline(body)}</p>")
                cells.append(f'<div class="card"><h3>{inline(f[0])}</h3><p class="def">{inline(f[1])}</p>{body_html}</div>')
            out.append(f'<div class="cards n{len(group)}">' + "".join(cells) + "</div>")
        elif gkind == "time":
            out.append('<ol class="timeline">' + "".join(
                f'<li><b>{inline(a)}</b><span>{inline(b)}</span></li>' for a, b in group) + "</ol>")
        elif gkind == "check":
            out.append('<ul class="checks">' + "".join(
                f'<li>{CHECK}<div><b>{inline(a)}</b><span>{inline(b)}</span></div></li>' for a, b in group) + "</ul>")
        elif gkind == "bars":
            out.append('<div class="charts">' + "".join(bars_svg(s) for s in group) + "</div>")
        elif gkind == "table":
            head, rows = group[0], group[1:]
            t = ['<div class="tablewrap"><table><thead><tr>' + "".join(f"<th>{inline(c)}</th>" for c in head) + "</tr></thead><tbody>"]
            for rw in rows:
                cls = ' class="total"' if rw[0] == "合計" else ""
                t.append(f"<tr{cls}>" + "".join(f"<td>{inline(c)}</td>" for c in rw) + "</tr>")
            out.append("".join(t) + "</tbody></table></div>")
        group, gkind = [], None

    def push(kind, item):
        nonlocal gkind
        if gkind != kind:
            flush()
            gkind = kind
        group.append(item)

    for ln in lines:
        if not ln.strip():
            continue
        if ln.startswith("::kpi "):
            push("kpi", parts(ln[6:]))
        elif ln.startswith("::step "):
            push("step", parts(ln[7:]))
        elif ln.startswith("::card "):
            push("card", parts(ln[7:]))
        elif ln.startswith("::time "):
            push("time", parts(ln[7:]))
        elif ln.startswith("::check "):
            push("check", parts(ln[8:]))
        elif ln.startswith("::bars "):
            push("bars", ln[7:])
        elif ln.startswith("::table "):
            flush()
            push("table", parts(ln[8:]))
        elif ln.startswith("::row "):
            group.append(parts(ln[6:]))
        elif ln.startswith("- "):
            push("ul", ln[2:])
        else:
            flush()
            if ln.startswith("::analogy "):
                lab, txt = parts(ln[10:])
                out.append(f'<aside class="analogy">{CAKE}<div><em>{inline(lab)}</em><p>{inline(txt)}</p></div></aside>')
            elif ln.startswith("::formula "):
                out.append(f'<div class="formula">{inline(ln[10:])}</div>')
            elif ln.startswith("::note "):
                out.append(f'<p class="note">{inline(ln[7:])}</p>')
            elif ln.startswith("::sub "):
                out.append(f'<p class="sub">{inline(ln[6:])}</p>')
            elif ln.startswith("::flow "):
                items = []
                for it in parts(ln[7:]):
                    hi = it.startswith("*")
                    a, b = parts(it.lstrip("*"), "/")
                    items.append(f'<li class="{"hi" if hi else ""}"><b>{inline(a)}</b><span>{inline(b)}</span>'
                                 + ('<i>矽格在這裡</i>' if hi else "") + "</li>")
                out.append('<ol class="flow">' + "".join(items) + "</ol>")
            else:
                out.append(f'<p class="lead">{inline(ln)}</p>')
    flush()
    return "".join(out)


def render_slide(path, idx, total):
    title, kicker, layout, cids, body = "", "", "", [], []
    started = False
    for ln in path.read_text(encoding="utf-8").splitlines():
        if not started:
            if ln.startswith("# "):
                title = ln[2:]
            elif ln.startswith("cards:"):
                cids = [c.strip() for c in ln[6:].split(",") if c.strip()]
            elif ln.startswith("kicker:"):
                kicker = ln[7:].strip()
            elif ln.startswith("layout:"):
                layout = ln[7:].strip()
            elif ln.strip() == "---":
                started = True
        else:
            body.append(ln)
    srcs = []
    for c in cids:
        name = Path(CARDS[c]["src"]).stem
        if name not in srcs:
            srcs.append(name)
    if layout == "split" and "||" in body:
        k = body.index("||")
        inner = (f'<div class="cols"><div class="col">{render_blocks(body[:k])}</div>'
                 f'<div class="col">{render_blocks(body[k + 1:])}</div></div>')
    else:
        inner = render_blocks(body)
    head_tag = "h1" if layout == "cover" else "h2"
    foot = (f'<footer><span class="src">出處：{"、".join(html.escape(s) for s in srcs)}'
            f'<small>（證據卡 {", ".join(cids)}）</small></span><span class="pg">{idx:02d} / {total:02d}</span></footer>')
    return (f'<section class="slide {layout}" id="s{idx}" data-cards="{",".join(cids)}" aria-label="第 {idx} 頁">'
            f'<div class="frame"><header><span class="kicker">{inline(kicker)}</span>'
            f'<{head_tag}>{inline(title)}</{head_tag}></header><div class="body">{inner}</div>{foot}</div></section>')


files = sorted((DECK / "drafts").glob("*.md"))
slides = "".join(render_slide(f, i + 1, len(files)) for i, f in enumerate(files))
tpl = (ROOT / "scripts" / "deck_template.html").read_text(encoding="utf-8")
page = tpl.replace("<!--SLIDES-->", slides).replace("__TOTAL__", str(len(files)))
# deck.html：發布成 Artifact 用（平台會自動包上 doctype/head）
(DECK / "deck.html").write_text(page, encoding="utf-8")
# index.html：完整 HTML 文件，本機或 GitHub Pages 直接開
(DECK / "index.html").write_text(
    '<!doctype html>\n<html lang="zh-Hant"><head><meta charset="utf-8">'
    '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
    + page.replace("<div id=\"viewport\">", "</head><body><div id=\"viewport\">", 1) + "\n</body></html>\n",
    encoding="utf-8")
print(f"rendered {len(files)} slides -> deck/deck.html, deck/index.html")
