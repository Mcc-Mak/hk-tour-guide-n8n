# 軟體需求規格書

本軟體需求規格書（Software Requirements Specification, SRS）詳述「香港建築物導賞手冊自動化流水線」的功能性需求、非功能性需求、系統約束、假設與依賴，以及需求優先級。本文件為設計與驗證的依據。

## 簡介

### 目的

本文件旨在為開發團隊、維運團隊與利害關係人提供明確、可驗證的需求基準，確保專案交付成果符合專案章程所訂定的願景與成功準則。所有需求均配置唯一識別碼，並於需求追溯矩陣（RTM）中映射至實作元件與驗證方式。

### 適用範圍

本規格涵蓋兩階段流水線：第一階段提示詞工作流（產出鷹架），第二階段 n8n 工作流（建築物迭代迴圈）。涵蓋 CrewAI 多代理系統、n8n 工作流引擎、Docker 容器化、GitHub Actions CI/CD、mdBook 文檔發佈及 GitHub 專案管理整合。

### 定義與縮寫

- **CrewAI** — 多代理協作框架，本專案的強制要求。
- **硬關卡（Hard Gate）** — 真實性審查機制，無來源陳述一律不通過。
- **原子化迭代** — 逐座建築物獨立處理，單座失敗不影響其他。
- **runs 目錄** — 每次迭代的中間狀態與日誌存放處。
- **fail-then-skip-building** — 審查五次未通過（1 次初試 + 4 次重試）時的跳過策略。

## 功能性需求

### FR-001 建築矩陣讀取

系統須能讀取 `codebase/建築矩陣.md` 作為建築物清單來源，解析每筆建築物的分類（法定古蹟／新界／市區）、中文名稱與中文地址，作為迭代迴圈的輸入。

### FR-002 CrewAI 歷史研究

系統須以 `archival_researcher` 代理執行歷史檔案研究，產出涵蓋建築基本資料、歷史背景、建築特色、文化意義的結構化報告，且所有事實陳述附可查證來源連結。

### FR-003 硬關卡可信度審查

系統須以 `credibility_assessor` 代理對研究報告執行硬關卡審查，檢查每項事實陳述是否有可驗證來源、來源是否權威、是否存在推測性陳述，並輸出 `passed` 或 `failed` 判定與信心分數。

### FR-004 重試與跳過策略

系統須於硬關卡審查失敗時最多嘗試五次（1 次初試 + 4 次重試，每次退避 5 秒）；五次仍未通過則執行 `fail-then-skip-building`，於 `runs/{building_id}/` 記錄 Exception Log，跳過後續步驟進入下一迴圈。

### FR-005 導賞手冊產出

系統須以 `documentation_writer` 代理將通過審查的研究轉化為 Markdown 導賞手冊，寫入正確分類路徑（`法定古蹟`／`新界`／`市區`），檔名遵循 `{編號}-{中文名稱}-{中文地址}.md`。

### FR-006 CHANGELOG 更新

系統須於每座建築物或每輪提示詞工作流完成後，於 `CHANGELOG` 追加一筆紀錄，並依變更級別（major／minor／patch）調升語意化版本號。

### FR-007 版本控制與推送

系統須僅 stage 該建築物的產出檔案，以規範化提交訊息提交，並推送至 `origin/dev-001`；嚴禁直接推送至 `dev` 或 `main`。

### FR-008 n8n Webhook 觸發

系統須提供 Webhook 端點（`POST /webhook/hk-building-tour`）供外部系統觸發流水線；n8n 僅由 Webhook 啟動，不設定 Cron 排程。

### FR-009 n8n 迭代迴圈

n8n 工作流須以 Loop 節點逐建築物迭代，每座建築物執行研究、審查、產出、CHANGELOG 更新、版本控制與狀態同步六步驟。

### FR-010 可觀測性

系統須配置 CrewAI `step_callback` 與 `task_callback` 捕捉中間思考與對話，寫入 `intermediate_research.json`；n8n 擷取 Python 腳本 stdout 日誌並載入 runs JSON 供狀態檢視與條件判斷。

### FR-011 專案經理狀態同步

系統須以 `pm_agent` 代理透過 `git_ops` 工具與 GitHub CLI 更新該建築物的 Issue 狀態為完成，並同步 Project 看板。

### FR-012 mdBook 部署

系統須於 CI/CD 通過品質閘門後，以 mdBook 編譯靜態文檔網站並自動部署。

### FR-013 提示詞工作流鷹架產出

提示詞工作流須產出 n8n 工作流 JSON、CrewAI 設定（agents、tasks、tools、config）、完整文檔集與 README，並將中介狀態寫入 `runs/prompt-workflow/intermediate_state.json`。

## 非功能性需求

### NFR-001 可信度

知識庫內容須 100% 通過硬關卡審查；未通過者不得進入知識庫，僅以 Exception Log 記錄。此為最高優先級的品質屬性。

### NFR-002 韌性

單座建築物失敗不得中斷整體迴圈；重試機制須在最多五次嘗試後（1 次初試 + 4 次重試）優雅降級為跳過，並保留完整日誌以供後續分析。

### NFR-003 可觀測性

所有代理的中間思考、對話與任務結果須結構化留存；n8n 須即時擷取 Python 腳本 stdout，並能依 runs JSON 內容進行條件分支判斷。

### NFR-004 可追溯性

每筆變更須可追溯至來源文檔、實作元件與驗證方式（見 RTM）；版本號、提交訊息與分支流動須遵循規範。

### NFR-005 安全性

CI/CD 須執行 CodeQL 與 SonarQube 掃描，要求零重大漏洞；金鑰與憑證須以環境變數或 GHA Secrets 注入，嚴禁寫入程式碼或提交至儲存庫。

### NFR-006 效能

CrewAI 設定 `max_rpm: 10` 以控制 LLM 呼叫呼叫頻率；單座建築物處理應於合理時間內完成，避免單一迭代阻塞整體進度。

### NFR-007 可維護性

代理角色、任務與工具須以 YAML 聲明式配置；文檔須持續與實作同步，任何變更須更新對應文檔與 CHANGELOG。

### NFR-008 可部署性

n8n 須以 Docker Compose 一鍵啟動；自建映像檔須包含 Python、CrewAI 依賴與 GitHub CLI；Webhook 須綁定可達主機。

## 系統約束

- 必須採用 CrewAI，嚴禁自定義手寫 Agent 取代。
- n8n 為自架 Docker Community Edition，綁定 `0.0.0.0:45678`，非 n8n Cloud。
- Cron 排程僅於 GitHub Actions（`0 9 * * *`，HKT 17:00），n8n 不設定排程。
- 分支流動固定為 `dev-001 → dev → main`，GHA 自動合併。
- GHA 僅有單一統合檔案 `gh-pipeline.yml`。
- 所有內容與文檔以繁體中文撰寫，建築物名稱保留中文。
- 授權為 MIT。

## 假設與依賴

- LLM 提供者（如 OpenAI）API 可用且金鑰有效。
- 搜尋 API（用於檔案研究）可用且金鑰有效。
- GitHub 儲存庫與 Project Board 存在且具備寫入權限。
- 建築矩陣來源資料具備合理的完整性與正確性。
- Docker 主機具備足夠資源運行 n8n 容器與 Python 腳本。
- mdBook 已安裝於 CI/CD 執行環境或可由 GHA 自動取得。

## 需求優先級

| 優先級 | 需求識別碼 | 說明 |
| --- | --- | --- |
| Must | FR-002, FR-003, FR-004, NFR-001 | 歷史研究與硬關卡審查為核心價值 |
| Must | FR-005, FR-007, FR-009 | 導賞手冊產出與版本控制閉環 |
| Must | FR-010, NFR-003 | 可觀測性確保流程可控 |
| Should | FR-001, FR-006, FR-008, FR-011 | 輸入讀取、CHANGELOG、觸發與狀態同步 |
| Should | FR-012, FR-013 | mdBook 部署與鷹架產出 |
| Should | NFR-002, NFR-005 | 韌性與安全性 |
| Could | NFR-006, NFR-007 | 效能調優與可維護性 |
| Could | NFR-008 | 一鍵部署便利性 |
