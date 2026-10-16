# 變更管理 — Recursive Agentic Sandbox (RAS)

本文件規範 RAS 基礎設施（Root 層）的變更管理。專案特定變更見 `codebase/docs/crm.md`。

## 變更流程

1. **建立 Issue** — 於 GitHub 建立對應變更的 Issue。
2. **執行動作** — 依治理工作流（W1 或 W2）執行實作與文檔更新。
3. **CHANGELOG** — 於統合 `CHANGELOG` 追加一筆紀錄，依變更級別調升語意化版本號。
4. **推送** — 推送至 `dev-001`，由 GHA 流水線依序合併至 `main`。
5. **關閉 Issue** — 流水線完成後由 PM 同步關閉。

## 版本號規範

遵循 `major.minor.patch`：

- `major` — 破壞性／架構性變更。
- `minor` — 新增功能或非破壞性變更。
- `patch` — 錯誤修復。

## 提交標題規範

- 提示詞工作流：`feat(scaffolding): {簡述產出內容}`
- 建築物：`feat(building): add biography and tour guide for {中文名稱}`

## 文件引用

- 根索引 → [`toc.md`](../toc.md)
- 專案章程 → [`charter.md`](charter.md)
- 全域變更記錄 → [`../CHANGELOG`](../CHANGELOG)