# 系統需求規格書 — Recursive Agentic Sandbox (RAS)

本文件描述 RAS 基礎設施（Root 層，Workflow-1）的系統需求。專案特定需求（Workflow-2）見 `codebase/docs/srs.md`。

## 功能需求

### FR-1 單一儲存庫
系統須位於單一 GitHub 儲存庫，於基礎設施（`./`）與實作（`codebase/`）之間邏輯分離。

### FR-2 治理分離
- Workflow-1 由 `./AGENTS.md` 治理，負責啟動階段（基礎設施與沙盒）。
- Workflow-2 由 `./codebase/AGENTS.md` 治理，負責專案階段。

### FR-3 容器化沙盒
- 須建置結合 n8n 執行環境與 Python 3.10+（含 AI 函式庫）的自訂 Docker 映像。
- `./codebase` 須綁定掛載至容器，確保代理變更持久化至主機儲存庫。

### FR-4 編排
- n8n 為觸發機制，依傳入請求或排程事件呼叫 CrewAI 代理執行 Workflow-2。
- 觸發器分離：n8n 僅由 Webhook／外部系統觸發；Cron 排程屬於 GitHub Actions。

### FR-5 版本控制
- 分支流動固定：`dev-001 -> dev -> main`；嚴禁直接推送至 `dev`／`main`。
- 統合 `CHANGELOG` 遵循語意化版本號。

## 非功能需求

### NFR-1 可稽核性
所有變更須經治理工作流，並於 CHANGELOG 留存統合稽核軌跡。

### NFR-2 可觀測性
CrewAI 執行須配置 step/task callback，將中間狀態寫入 runs 目錄。

### NFR-3 文件標準
根目錄文檔（`docs/`）描述基礎設施；`codebase/docs/` 描述專案。

## 文件引用

- 根索引 → [`toc.md`](../toc.md)
- 專案章程 → [`charter.md`](charter.md)