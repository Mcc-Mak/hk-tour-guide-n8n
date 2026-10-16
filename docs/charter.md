# 專案章程 — Recursive Agentic Sandbox (RAS)

## 概述

本儲存庫為一套**遞迴代理沙盒（Recursive Agentic Sandbox, RAS）**：一個自我引導的開發環境，透過巢狀 AI 代理工作流自動化軟體專案的生命週期。系統採用「種子儲存庫」方式，由主編排層（Workflow-1）建置一個容器化的 n8n + CrewAI 沙盒，該沙盒再執行次級實作層（Workflow-2）以建置與維護特定專案。

## 目標

1. 提供一個可重現、可稽核的自動化開發環境。
2. 透過單一統合 GitHub 儲存庫，於基礎設施（Root）與實作（Codebase）之間進行邏輯分離。
3. 以 n8n 編排 + CrewAI 代理推理自動化專案生命週期。

## 範疇

- **Workflow-1（啟動階段）：** 實例化基礎設施與容器化沙盒，受 `AGENTS.md`（Root）治理。
- **Workflow-2（專案階段）：** 於沙盒內執行專案特定迭代，受 `codebase/AGENTS.md` 治理。

## 授權

MIT。所有文檔與內容以繁體中文撰寫。

## 文件引用

- 根索引 → [`toc.md`](../toc.md)
- 系統需求 → [`srs.md`](srs.md)
- 變更管理 → [`crm.md`](crm.md)
- 專案治理 → [`../AGENTS.md`](../AGENTS.md)