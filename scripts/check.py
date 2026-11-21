"""矽格 LLM Wiki 程式檢查（AGENTS.md 第 5 節：A／B／C／E／F）

用法：  py scripts/check.py
讀取 wiki/data/*.csv，輸出 wiki/data/check_report.md，並把換算結果寫到 wiki/data/mix_derived.csv。
有 FAIL 時 exit code = 1。
"""
import csv
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "wiki" / "data"

results = []  # (code, status, message)


def add(code, ok, msg, warn=False):
    status = "PASS" if ok else ("WARN" if warn else "FAIL")
    results.append((code, status, msg))


def read(name):
    p = DATA / name
    if not p.exists():
        return []
    with p.open(encoding="utf-8") as f:
        return [r for r in csv.DictReader(f) if any(v.strip() for v in r.values())]


def num(x):
    return float(str(x).replace(",", "")) if str(x).strip() not in ("", "-") else None


# ---------- 產品組合（億元） ----------
mix = read("product_mix.csv")
periods = defaultdict(dict)   # period -> key -> row
for r in mix:
    periods[r["period"]][r["key"]] = r

for period, rows in periods.items():
    if "total" not in rows:
        add("A", False, f"{period}：缺少合計列")
        continue
    total = num(rows["total"]["amount"])
    items = {k: v for k, v in rows.items() if k != "total"}
    s = sum(num(v["amount"]) for v in items.values())
    add("A", abs(s - total) <= 0.05,
        f"{period}：各應用加總 {s:.2f} 億 vs 合計 {total:.2f} 億（差 {s - total:+.2f}）")
    pct = sum(num(v["label_pct"]) for v in items.values())
    add("A", 98 <= pct <= 102, f"{period}：標示占比加總 {pct:.0f}%")
    for k, v in items.items():
        calc = num(v["amount"]) / total * 100
        lab = num(v["label_pct"])
        add("F", abs(calc - lab) <= 1.0,
            f"{period} {v['label']}：{v['amount']} 億 ÷ 合計 = {calc:.1f}% vs 圖上標示 {lab:.0f}%")

# ---------- C：累計 → 單期換算 ----------
DERIVE = [  # (新期間, 較長累計, 較短累計)
    ("2026-06~08", "2026-01~08", "2026-01~05"),
    ("2025-06~08", "2025-01~08", "2025-01~05"),
]
derived_rows = []
for new, long_, short in DERIVE:
    if long_ not in periods or short not in periods:
        continue
    L, S = periods[long_], periods[short]
    tot = num(L["total"]["amount"]) - num(S["total"]["amount"])
    s = 0.0
    for k in L:
        if k == "total":
            continue
        if k not in S:
            add("C", False, f"{new}：{k} 在 {short} 找不到對應分類")
            continue
        d = num(L[k]["amount"]) - num(S[k]["amount"])
        s += d
        add("C", d >= 0, f"{new} {L[k]['label']}：{L[k]['amount']} − {S[k]['amount']} = {d:.2f} 億（不得為負）")
        derived_rows.append({"period": new, "key": k, "label": L[k]["label"],
                             "amount": f"{d:.2f}", "pct": f"{d / tot * 100:.1f}",
                             "formula": f"{long_} − {short}"})
        # E：口徑檢查
        if L[k]["label"] != S[k]["label"]:
            add("E", False, f"{new}：分類名稱改變「{S[k]['label']}」→「{L[k]['label']}」，相減前需註記口徑", warn=True)
    add("C", abs(s - tot) <= 0.05, f"{new}：換算後加總 {s:.2f} 億 vs 合計相減 {tot:.2f} 億")
    derived_rows.append({"period": new, "key": "total", "label": "合計", "amount": f"{tot:.2f}",
                         "pct": "100.0", "formula": f"{long_} − {short}"})

if derived_rows:
    with (DATA / "mix_derived.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["period", "key", "label", "amount", "pct", "formula"])
        w.writeheader()
        w.writerows(derived_rows)

# ---------- F：損益表恆等式（百萬元） ----------
fin = read("financials.csv")
for r in fin:
    p = f"{r['period']}（{r['source']}）"
    rev, cogs, gp = num(r["revenue"]), num(r["cogs"]), num(r["gross_profit"])
    opex, op, nonop = num(r["opex"]), num(r["op_income"]), num(r["non_op"])
    pre, tax, ni = num(r["pretax"]), num(r["tax"]), num(r["net_income"])
    add("F", abs(rev - cogs - gp) <= 1.5, f"{p}：營收 {rev:,.0f} − 成本 {cogs:,.0f} = 毛利 {gp:,.0f}")
    add("F", abs(gp - opex - op) <= 1.5, f"{p}：毛利 − 費用 {opex:,.0f} = 營業利益 {op:,.0f}")
    add("F", abs(op + nonop - pre) <= 1.5, f"{p}：營業利益 + 業外 {nonop:,.0f} = 稅前 {pre:,.0f}")
    add("F", abs(pre - tax - ni) <= 1.5, f"{p}：稅前 − 所得稅 {tax:,.0f} = 本期淨利 {ni:,.0f}")
    if r.get("gm_label"):
        add("F", abs(gp / rev * 100 - num(r["gm_label"])) <= 0.15,
            f"{p}：毛利率 {gp / rev * 100:.1f}% vs 報表標示 {num(r['gm_label']):.1f}%")

# ---------- B：跨來源核對 ----------
monthly = read("monthly_revenue.csv")   # 千元
cum = {r["ym"]: num(r["cum"]) for r in monthly}
mon = {r["ym"]: num(r["revenue"]) for r in monthly}

# B1：月營收累計 vs 法說會產品組合合計
for period, rows in periods.items():
    y, rng = period.split("-")
    end = int(rng.split("~")[1])
    ym = f"{y}-{end:02d}"
    if ym in cum and "total" in rows:
        a, b = cum[ym] / 1e5, num(rows["total"]["amount"])
        add("B", abs(a - b) <= 0.01, f"{period}：月營收累計 {a:.2f} 億 vs 法說會合計 {b:.2f} 億")

# B2：季度營收 vs 該季月營收加總
for r in fin:
    if r["period"].startswith("2026Q") and len(r["period"]) == 6:
        q = int(r["period"][-1])
        ms = [f"2026-{m:02d}" for m in range(3 * q - 2, 3 * q + 1)]
        if all(m in mon for m in ms):
            s = sum(mon[m] for m in ms) / 1e3
            add("B", abs(s - num(r["revenue"])) <= 1.5,
                f"{r['period']}：季營收 {num(r['revenue']):,.0f} 百萬 vs 月營收加總 {s:,.0f} 百萬")

# B3：Q1+Q2+Q3 vs 前三季累計
fp = {r["period"]: r for r in fin}
if all(k in fp for k in ("2026Q1", "2026Q2", "2026Q3", "2026-9M")):
    for col, name in (("revenue", "營收"), ("gross_profit", "毛利"), ("net_income", "本期淨利")):
        s = sum(num(fp[k][col]) for k in ("2026Q1", "2026Q2", "2026Q3"))
        t = num(fp["2026-9M"][col])
        add("B", abs(s - t) <= 3, f"{name}：Q1+Q2+Q3 = {s:,.0f} 百萬 vs 前三季財報 {t:,.0f} 百萬（差 {s - t:+.0f}，四捨五入）")
    s = sum(num(fp[k]["eps_basic"]) for k in ("2026Q1", "2026Q2", "2026Q3"))
    add("B", abs(s - num(fp["2026-9M"]["eps_basic"])) <= 0.02,
        f"基本 EPS：Q1+Q2+Q3 = {s:.2f} 元 vs 前三季 {num(fp['2026-9M']['eps_basic']):.2f} 元")

# ---------- 輸出 ----------
lines = ["# 檢查報告（scripts/check.py 自動產生）", "",
         "| 代號 | 結果 | 內容 |", "|---|---|---|"]
icon = {"PASS": "✅", "WARN": "⚠️", "FAIL": "❌"}
for code, st, msg in results:
    lines.append(f"| {code} | {icon[st]} {st} | {msg} |")
cnt = {s: sum(1 for _, x, _ in results if x == s) for s in ("PASS", "WARN", "FAIL")}
lines += ["", f"合計：PASS {cnt['PASS']}／WARN {cnt['WARN']}／FAIL {cnt['FAIL']}"]
(DATA / "check_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

sys.stdout.reconfigure(encoding="utf-8")
for code, st, msg in results:
    if st != "PASS":
        print(f"[{code}] {st}: {msg}")
print(f"PASS {cnt['PASS']} / WARN {cnt['WARN']} / FAIL {cnt['FAIL']}  -> wiki/data/check_report.md")
sys.exit(1 if cnt["FAIL"] else 0)
