# log.md — Ingest 與檢查紀錄

> 每次 ingest 一份資料記一筆：新增/更新的頁面、檢查結果（A／B／C／E／F）、發現的問題與處理方式。

## 2026-11-21 ｜ setup

- 依需求訪談（`notes/需求訪談紀錄.md`）建立 `AGENTS.md`、`CLAUDE.md`、資料夾結構。
- 8 份原始資料移入 `raw/` 並改成「日期_名稱」格式；新聞 HTML 以 `.gitignore` 排除，不推上 GitHub。
- 建立 `scripts/check.py`（A／B／C／E／F 程式檢查）與空的 `wiki/data/*.csv`。
- 檢查：無資料，PASS 0 / WARN 0 / FAIL 0。

## 2026-11-21 ｜ ingest #1：2025 年報

- **新增**：sources/2025年報、concepts/IC測試是什麼、晶圓測試與成品測試、系統級測試與預燒、封測產業鏈、3A策略、company/矽格公司概覽、擴廠與資本支出、data/財務數據總表
- **數據**：financials.csv 新增 2024-FY、2025-FY
- **檢查**：PASS 8 / WARN 0 / FAIL 0（F 損益恆等式 ×8）
- **問題**：
  - PDF 轉文字後「營業比重」表的標籤被拆成直排、數字跨欄 → 人工以「各項加總 = 合計」驗證（19,587,196 千元 ✅）後才寫入。
  - 年報說毛利率「29%」，計算為 29.2% → 年報是四捨五入，`gm_label` 留空不比對。
