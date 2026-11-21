# log.md — Ingest 與檢查紀錄

> 每次 ingest 一份資料記一筆：新增/更新的頁面、檢查結果（A／B／C／E／F）、發現的問題與處理方式。

## 2026-11-21 ｜ setup

- 依需求訪談（`notes/需求訪談紀錄.md`）建立 `AGENTS.md`、`CLAUDE.md`、資料夾結構。
- 8 份原始資料移入 `raw/` 並改成「日期_名稱」格式；新聞 HTML 以 `.gitignore` 排除，不推上 GitHub。
- 建立 `scripts/check.py`（A／B／C／E／F 程式檢查）與空的 `wiki/data/*.csv`。
- 檢查：無資料，PASS 0 / WARN 0 / FAIL 0。
