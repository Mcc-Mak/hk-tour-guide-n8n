# 產品設計文件

本產品設計文件（Product Design Document, PDR）描述「香港建築物導賞手冊自動化流水線」的架構概覽、資料流程、組件設計、技術棧與介面設計，作為工程實作的藍圖。

## 架構概覽

本專案採兩階段架構，以「鷹架→生產」模式確保可控演進。兩階段皆受 GitHub 分支管線管控，遵循固定分支流動 `dev-001 → dev → main`。

### 第一階段：提示詞工作流（Prompt Workflow）

提示詞工作流為專案鷹架階段，由 CrewAI 產出 n8n 工作流 JSON、`.crewai/` 設定（agents、tasks、tools、config）與完整文檔集。此階段不處理建築物，而是建立第二階段所需的全部基礎設施與文檔。產出成熟後方可安裝 n8n 並啟動建築物迭代迴圈。

提示詞工作流六步驟：PM 與狀態準備 → 產出原始碼 by CrewAI → 產出文檔 by CrewAI → 更新 CHANGELOG → 即時版本控制與推送至 `dev-001` → PM 狀態同步。中介狀態寫入 `codebase/.crewai/runs/prompt-workflow/intermediate_state.json`。

### 第二階段：n8n 工作流（建築物迭代迴圈）

n8n 工作流為生產階段，於提示詞工作流產出成熟後啟動。每座建築物以原子化方式處理，單座失敗不中斷整體迴圈。n8n 僅由 Webhook 觸發，Cron 排程屬於 GitHub Actions。

n8n 工作流六步驟：PM 與狀態準備 → CrewAI 研究與硬關卡（失敗最多嘗試五次，1 次初試 + 4 次重試，仍未通過則 `fail-then-skip-building`）→ 產出導賞手冊與文檔 → 更新 CHANGELOG → 即時版本控制與推送至 `dev-001` → PM 狀態同步。中介狀態寫入 `codebase/.crewai/runs/{building_id}/intermediate_research.json`。

### 架構分層

- **觸發層** — n8n Webhook（外部系統觸發）+ GitHub Actions cron（排程品質檢查與部署）。
- **編排層** — n8n 工作流（Loop 迭代、Execute Command、狀態載入）。
- **代理層** — CrewAI 多代理（archival_researcher、credibility_assessor、documentation_writer、pm_agent）。
- **工具層** — CrewAI 工具（web_search、file_writer、git_ops）。
- **儲存層** — 檔案系統（導賞手冊 Markdown、runs JSON、CHANGELOG）+ Git 儲存庫。
- **發佈層** — mdBook 靜態網站 + GitHub Pages（或同等部署目標）。
- **治理層** — GitHub Actions 流水線（分支推進、品質閘門、PM 審查）。

## 資料流程

### 提示詞工作流資料流

1. 觸發提示詞工作流（人工或腳本啟動）。
2. CrewAI 讀取 AGENTS.md 與建築矩陣作為上下文。
3. 產出 `codebase/.n8n/hk-building-biography-workflow.json`。
4. 產出 `codebase/.crewai/`（agents.yaml、tasks.yaml、config.yaml、tools/、requirements.txt）。
5. 產出 `codebase/docs/*.md`、`codebase/toc.md`、`README.md`。
6. 更新 CHANGELOG，提交並推送至 `dev-001`。
7. 中介狀態寫入 `runs/prompt-workflow/intermediate_state.json`。

### n8n 建築物迭代資料流

1. 外部系統 POST 至 n8n Webhook `/webhook/hk-building-tour`。
2. n8n 讀取 `建築矩陣.md`，解析建築物清單。
3. Loop 逐建築物迭代：
   - n8n `Execute Command` 呼叫 `python crew.py --building-id {id}`。
   - `archival_researcher` 執行研究，產出 JSON 研究報告。
   - `credibility_assessor` 執行硬關卡審查；失敗最多重試四次（1 次初試 + 4 次重試，共五次嘗試）。
   - 通過則 `documentation_writer` 產出 Markdown 並寫入分類路徑。
   - 中介狀態寫入 `runs/{building_id}/intermediate_research.json`。
   - n8n 擷取 stdout 日誌並載入 runs JSON 供條件判斷。
   - 更新 CHANGELOG，`git_ops` stage + 提交 + 推送至 `dev-001`。
   - `pm_agent` 更新 GitHub Issue 與 Project 看板。
4. 五次未通過則記錄 Exception Log 並跳過，進入下一座。
5. GHA 偵測 `dev-001` 推送，自動合併至 `dev` 再至 `main`。
6. 於 `main` 執行品質掃描，通過後 mdBook 部署。

## 組件設計

### CrewAI 代理

| 代理 | 角色 | 職責 | 工具 |
| --- | --- | --- | --- |
| archival_researcher | 歷史檔案研究員 | 產出附來源的研究報告 | web_search |
| credibility_assessor | 可信性評估員 | 硬關卡真實性審查 | — |
| documentation_writer | 導賞手冊撰寫員 | 產出 Markdown 導賞手冊 | file_writer |
| pm_agent | 專案經理 | 更新 GitHub Issue 與 Project | git_ops |

Crew 採循序（sequential）執行，配置 `memory: true`、`max_rpm: 10`、`verbose: true`。重試 `max_attempts: 3`、`backoff_seconds: 5`。

### CrewAI 任務

- `research_task` — 歷史檔案研究，產出 JSON（building_info、historical_context、architectural_features、cultural_significance、sources）。
- `credibility_task` — 硬關卡審查，產出 JSON（verdict、issues、confidence_score）。
- `documentation_task` — 撰寫 Markdown 並寫入分類路徑。
- `pm_sync_task` — 同步 GitHub Issue 與 Project 看板。

### n8n 工作流節點

- **Webhook** — 接收外部觸發。
- **Read File** — 讀取建築矩陣。
- **Loop** — 逐建築物迭代。
- **Execute Command** — 呼叫 Python CrewAI 腳本，擷取 stdout。
- **Read JSON** — 載入 runs JSON 供條件判斷。
- **If** — 依審查 verdict 分支（通過 / 跳過）。
- **Git** — stage、提交、推送（經 `git_ops` 或 shell）。
- **HTTP Request** — 呼叫 GitHub API 更新 Issue／Project。

## 技術棧

| 層 | 技術 | 用途 |
| --- | --- | --- |
| 多代理 | CrewAI ≥0.70.0 | 歷史研究與可信度審查 |
| 工具 | crewai-tools ≥0.12.0 | web_search 等工具 |
| 編排 | n8n Community Edition | 工作流迭代迴圈 |
| 容器 | Docker + Docker Compose | n8n 自架環境 |
| CI/CD | GitHub Actions | 分支推進、品質閘門、部署 |
| 程式碼掃描 | CodeQL + SonarQube | 零重大漏洞 |
| 文檔 | mdBook | 靜態文檔網站 |
| 版本控制 | Git + GitHub CLI (gh) | 提交、推送、Issue 管理 |
| LLM | OpenAI（gpt-4o） | 代理推理 |
| 語言 | Python 3 | CrewAI 腳本 |

## 介面設計

### 外部介面

- **n8n Webhook** — `POST /webhook/hk-building-tour`，JSON body 含觸發參數（可選建築物範圍）。
- **GitHub API** — Issue 狀態更新與 Project 看板同步，以 `GITHUB_TOKEN` 認證。
- **LLM API** — OpenAI API，以 `OPENAI_API_KEY` 認證。
- **搜尋 API** — 檔案研究用，以 `SEARCH_API_KEY` 認證。

### 內部介面

- **CrewAI CLI** — `crew.py` 接受 `--building-id` 參數，stdout 輸出 JSON 日誌。
- **runs JSON** — `intermediate_research.json` 作為 n8n 與 CrewAI 間的狀態契約。
- **檔案系統契約** — 導賞手冊路徑 `導賞手冊/{分類}/{編號}-{中文名稱}-{中文地址}.md`。

### mdBook 介面

mdBook 以 `codebase/toc.md` 為 SUMMARY，編譯為多頁靜態網站。導航分為：簡介、快速開始、建築矩陣、文檔集（14 份）。樣式採 mdBook 預設主題，確保行動裝置可讀性。

### 可觀測性介面

- `step_callback` / `task_callback` 將代理思考與任務結果結構化寫入 runs JSON。
- n8n 透過 stdout 擷取 Python 日誌，即時顯示於執行畫面並供後續節點條件判斷。
- GitHub Project 看板提供整體進度視覺化。
