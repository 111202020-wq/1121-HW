"""簡報 workflow 的檢查關卡（.agents/workflows/topic-slides.md）

用法：
  py scripts/check_deck.py coverage   關卡1：必要 wiki 頁都被檢索到
  py scripts/check_deck.py cards      關卡2：每張證據卡的引文逐字存在於來源 wiki 頁
  py scripts/check_deck.py outline    關卡3：8–15 頁、每頁都有卡、卡都存在
  py scripts/check_deck.py drafts     關卡4：逐頁稿的每個數字，都在該頁引用的卡裡找得到
  py scripts/check_deck.py all
結果附加到 deck/check_log.md；有 FAIL 時 exit 1。
"""
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DECK = ROOT / "deck"
sys.stdout.reconfigure(encoding="utf-8")

REQUIRED = sorted(
    [p for d in ("concepts", "company", "data") for p in (ROOT / "wiki" / d).glob("*.md")
     if p.name != "check_report.md"]
    + [ROOT / "wiki" / "quarters" / "2026Q3.md"]
)


def norm(s):
    s = s.replace("**", "").replace("`", "")
    return re.sub(r"\s+", "", s)


def rel(p):
    return p.relative_to(ROOT).as_posix()


def load_cards():
    """回傳 {卡號: {"src": 路徑, "quote": 引文}}"""
    cards = {}
    for f in sorted((DECK / "cards").glob("*.md")):
        src, cur = None, None
        for line in f.read_text(encoding="utf-8").splitlines():
            if line.startswith("來源："):
                src = line[3:].strip()
            elif line.startswith("## "):
                cur = line[3:].strip()
                cards[cur] = {"src": src, "quote": "", "file": f.name}
            elif line.startswith("> ") and cur:
                cards[cur]["quote"] += line[2:].strip()
    return cards


def gate_coverage(out):
    text = (DECK / "sources.md").read_text(encoding="utf-8")
    ok = True
    for p in REQUIRED:
        hit = rel(p) in text
        ok &= hit
        out.append(("覆蓋率", hit, f"{rel(p)} {'已檢索' if hit else '未檢索'}"))
    return ok


def gate_cards(out):
    cards = load_cards()
    ok = True
    used_src = set()
    for cid, c in cards.items():
        src = ROOT / c["src"] if c["src"] else None
        if not src or not src.exists():
            out.append(("引文", False, f"{cid}：來源檔不存在 {c['src']}"))
            ok = False
            continue
        used_src.add(c["src"])
        hit = norm(c["quote"]) in norm(src.read_text(encoding="utf-8"))
        ok &= hit
        out.append(("引文", hit, f"{cid}（{c['src']}）引文{'逐字相符' if hit else '在來源頁找不到'}"))
    for p in REQUIRED:
        hit = rel(p) in used_src
        ok &= hit
        out.append(("覆蓋率", hit, f"{rel(p)} {'有' if hit else '沒有'}證據卡"))
    return ok


def parse_outline():
    slides, cur = [], None
    for line in (DECK / "outline.md").read_text(encoding="utf-8").splitlines():
        m = re.match(r"^## (\d+)\s+(.*)", line)
        if m:
            cur = {"no": int(m.group(1)), "title": m.group(2), "cards": []}
            slides.append(cur)
        elif cur and line.startswith("- 卡片："):
            cur["cards"] = [c.strip() for c in line[5:].split(",") if c.strip()]
    return slides


def gate_outline(out):
    cards = load_cards()
    slides = parse_outline()
    ok = 8 <= len(slides) <= 15
    out.append(("大綱", ok, f"頁數 {len(slides)}（需 8–15）"))
    for s in slides:
        if not s["cards"]:
            out.append(("大綱", False, f"第 {s['no']} 頁「{s['title']}」沒有引用證據卡"))
            ok = False
        for c in s["cards"]:
            if c not in cards:
                out.append(("大綱", False, f"第 {s['no']} 頁引用不存在的卡 {c}"))
                ok = False
    if ok:
        out.append(("大綱", True, f"{len(slides)} 頁都有引用卡，且卡都存在"))
    return ok


NUM = re.compile(r"\d[\d,]*(?:\.\d+)?")
META = ("cards:", "kicker:", "layout:")


def gate_drafts(out):
    cards = load_cards()
    ok = True
    files = sorted((DECK / "drafts").glob("*.md"))
    for f in files:
        lines = f.read_text(encoding="utf-8").splitlines()
        cids = []
        body = []
        for ln in lines:
            if ln.startswith("cards:"):
                cids = [c.strip() for c in ln[6:].split(",") if c.strip()]
            elif not ln.startswith(META):
                body.append(ln)
        missing = [c for c in cids if c not in cards]
        if missing or not cids:
            out.append(("忠實度", False, f"{f.name}：引用卡不存在或沒有引用 {missing}"))
            ok = False
            continue
        pool = norm("".join(cards[c]["quote"] for c in cids)).replace(",", "")
        bad = []
        for n in NUM.findall("\n".join(body)):
            key = n.replace(",", "")
            if key not in pool:
                bad.append(n)
        if bad:
            ok = False
            out.append(("忠實度", False, f"{f.name}：數字在引用卡中找不到 → {sorted(set(bad))}"))
        else:
            out.append(("忠實度", True, f"{f.name}：所有數字都能對到卡片 {', '.join(cids)}"))
    return ok


GATES = {"coverage": gate_coverage, "cards": gate_cards, "outline": gate_outline, "drafts": gate_drafts}

if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    names = list(GATES) if which == "all" else [which]
    out, all_ok = [], True
    for n in names:
        all_ok &= GATES[n](out)
    fails = [o for o in out if not o[1]]
    for g, okv, msg in out:
        if not okv:
            print(f"[{g}] FAIL: {msg}")
    print(f"{which}: PASS {len(out) - len(fails)} / FAIL {len(fails)}")
    with (DECK / "check_log.md").open("a", encoding="utf-8") as lf:
        lf.write(f"\n### {datetime.now():%Y-%m-%d %H:%M} ｜ {which}：PASS {len(out) - len(fails)} / FAIL {len(fails)}\n")
        for g, okv, msg in fails:
            lf.write(f"- ❌ [{g}] {msg}\n")
    sys.exit(0 if all_ok else 1)
