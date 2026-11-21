# 矽格（6257）LLM Wiki

依 Karpathy 的 LLM Wiki 構想，用「先討論、後生成」方式建立的個股知識庫。讀者設定為**投研新人與同學**。

## 從哪裡開始看

| 想看什麼 | 檔案 |
|---|---|
| 目錄 | [index.md](index.md) |
| AI 維護規則 | [AGENTS.md](AGENTS.md) |
| 需求訪談（先討論） | [notes/需求訪談紀錄.md](notes/需求訪談紀錄.md) |
| 每次 ingest 的檢查紀錄 | [log.md](log.md) |
| 自動檢查結果 | [wiki/data/check_report.md](wiki/data/check_report.md) |
| 核心痛點：累計產品組合 → 單期換算 | [wiki/data/產品組合追蹤.md](wiki/data/產品組合追蹤.md) |
| **教學 HTML 簡報** | [deck/index.html](deck/index.html)（線上版：https://claude.ai/artifact/2LK9bokXx8WGEwSeJXGbXH） |
| 簡報 workflow（graph） | [.agents/workflows/topic-slides.md](.agents/workflows/topic-slides.md) |
| 簡報執行與檢查報告 | [deck/report.md](deck/report.md) |

## 資料來源（8 份，每份一次 ingest、一個 commit）

2025 年報、2026.06.23 法說會、2026.10.06 法說會、2026 Q3 合併財報、2026 月營收、新聞 ×3（只放摘要與原文連結）

## 流程

```
raw/ 讀一份資料 → 寫 sources 摘要 → 更新 wiki 頁面與 CSV
   → py scripts/check.py（A 加總／B 跨來源／C 換算／E 口徑／F 數字對位）
   → 不通過就回頭修正（ingest #4、#5 各跑了 2 輪）
   → 更新 index.md、log.md → git commit
```

## 重跑檢查

```
py scripts/check.py
```
