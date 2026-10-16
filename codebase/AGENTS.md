# AGENTS.md — Workflow-2 專案治理（香港建築物導賞手冊）

本檔治理 **Workflow-2（專案階段）**：於 Workflow-1 建置的 n8n + CrewAI 沙盒內，執行產生香港建築物導賞手冊的端到端流水線。本專案為一套**端到端自動化流水線**，以 CrewAI 執行歷史研究與真實性可信度評估，透過 n8n 工作流引擎編排每座建築物的原子化迭代迴圈，並以 mdBook 編譯及發佈靜態文檔網站，全流程由 GitHub Actions CI/CD 流水線統一管控分支推進、品質掃描與自動部署。

> 上層治理（Workflow-1 啟動階段）見 [`../AGENTS.md`](../AGENTS.md)。

## 兩階段架構

本專案分兩階段：**提示詞工作流（Prompt Workflow）** 先由 CrewAI 產出專案鷹架（n8n 工作流 JSON、`.crewai/` 設定、文檔、README 等）；待產出成熟後安裝 n8n，**n8n 工作流** 負責編排每座建築物的迭代迴圈 — 每次迭代執行 CrewAI crew 進行歷史研究與真實性硬關卡（Hard Gate）審查，生成 Markdown、更新 CHANGELOG、提交並推送。mdBook 透過 GitHub Actions 發佈靜態文檔網站。兩階段皆受 GitHub 分支管線管控。

## 硬性約束（Codebase 層）

- **CrewAI 為強制要求。** 嚴禁以自定義手寫 Agent 取代。Crew 以 Python 腳本形式由 n8n 的 `Execute Command` 節點呼叫執行。
- **觸發器分離：** n8n 僅透過 Webhook／外部系統觸發啟動。Cron 排程屬於 GitHub Actions（`0 9 * * *` = HKT 17:00），**不在** n8n 中設定。
- **n8n 工作流重新匯入後必須重啟容器再發佈。** 重新匯入工作流後，舊工作流的 Webhook 路徑仍殘留於 n8n 記憶體快取，導致「Conflicting Webhook Path」錯誤。**標準流程：** (1) 清空舊工作流 → (2) `n8n import:workflow` → (3) **`docker restart`** 清除快取 → (4) 使用者於 UI 發發佈。嚴禁跳過重啟步驟。
- **n8n Community edition 啟用限制：** `NODES_EXCLUDE=[]` 必須設定（Execute Command 節點預設被封鎖）。`N8N_SECURE_COOKIE=false` 必須設定（HTTP 存取）。API 金鑰需於 UI 內建立（`N8N_API_KEY` 環境變數不被公共 API 接受）。
- **分支流動固定：`dev-001 -> dev -> main`。** 每座建築物的提交推送至 `dev-001`；GHA 流水線自動依序合併至 `main`。嚴禁直接推送至 `dev`／`main`。
- **提示詞工作流提交標題：** `feat(scaffolding): {簡述產出內容}`（清晰標題 + body）。僅 stage 該輪產出檔案。
- **每座建築物提交標題：** `feat(building): add biography and tour guide for {中文名稱}`（清晰標題 + body）。僅 stage 該建築物的產出檔案。
- **CHANGELOG** 遵從語意化版本號（`major.minor.patch`）；每座建築物或每輪提示詞工作流追加一筆紀錄並依變更級別調升版號。

## LLM 模型策略

使用兩個自架 LLM 模型，透過 HKO LiteLLM Proxy（`https://litellm.services.hko.gov.hk/`，OpenAI 兼容端點）存取，共用同一把 `HKO_API_KEY`。

| 環境變數 | 模型 | 用途 |
| --- | --- | --- |
| `HKO_LLM_PRIMARY` | `zai-org/GLM-5.2-FP8` | CrewAI 團隊主力模型（第 1–3 次嘗試） |
| `HKO_LLM_FALLBACK` | `deepseek-ai/DeepSeek-V4-Flash-0731-Coding` | CrewAI 第 4–5 次重試、格式修復、所有非 CrewAI 提示 |

- **CrewAI 重試模型切換：** 每次迭代最多 **5 次**嘗試；若其中一次例外／錯誤則直接退出該次，進入下一次。第 1–3 次使用 `HKO_LLM_PRIMARY`；第 4–5 次所有代理人切換至 `HKO_LLM_FALLBACK`。由 `config.yaml` 的 `retry.max_attempts: 5` 與 `retry.fallback_from_attempt: 4` 控制。
- **每次嘗試目的相同：** 第 1–5 次嘗試皆執行完全相同的 Crew 流程（同一批 Agent／Task，僅模型不同），**不得**因嘗試次數而漂移任務目的。
- **成功即中止（Short-circuit）：** 任一次嘗試通過硬關卡即立即成功收尾並**停止後續嘗試**（例如第 1 次成功→第 2–5 次全部跳過；第 1–2 次失敗、第 3 次成功→第 4–5 次跳過）。由 `crew.py` 在 `verdict == "passed"` 時立即 `sys.exit(0)` 實現。
- **單次工作流內不切換模型：** 每次嘗試以單一模型跑完整個 Crew 流程，流程進行中嚴禁中途更換模型。模型切換只發生在第 4、5 次嘗試的**開頭**。
- **非 CrewAI 提示：** 所有 CrewAI 團隊以外的 LLM 呼叫均使用 `HKO_LLM_FALLBACK`。
- **格式修復（Format Fixer）：** 硬關卡通過後，對產出的 Markdown 執行格式修復（`HKO_LLM_FALLBACK`，`temperature: 0`）。僅修復格式問題（含表格欄位漂移），**嚴禁新增、刪除或修改任何內容**。透過 `openai` Python 函式庫直接呼叫，不經過 CrewAI。

## 目錄結構（精確路徑 — 保留中文名稱）

- `建築矩陣.md` — 主建築物清單／矩陣（輸入來源）
- `導賞手冊/法定古蹟/{00001-99999}-{中文名稱}-{中文地址}.md`
- `導賞手冊/建築/新界/{00001-99999}-{中文名稱}-{中文地址}.md`
- `導賞手冊/建築/市區/{00001-99999}-{中文名稱}-{中文地址}.md`
- `.crewai/` — CrewAI Agent、Tasks、Tools 及設定檔
- `.crewai/runs/{building_id}/` — 每次迭代的中間狀態與日誌（含 `intermediate_research.json`）
- `.n8n/hk-building-biography-workflow.json` — n8n 工作流
- `docs/*.md` — 完整集合：`charter, user-stories, srs, prd, pdr, adr, api, schema, edr, configurations, deployment, settings, quick-start, rtm, crm`
- `site/` — mdBook 輸出（`book.toml`、`src/`、`SUMMARY.md`）
- `toc.md` — 目錄樹

## 提示詞工作流（Prompt Workflow — 6 步驟，依序執行）

提示詞工作流為專案鷹架階段，由 CrewAI 產出 n8n 工作流、`.crewai/` 設定與完整文檔；產出成熟後方可安裝 n8n 並啟動建築物迭代迴圈。

1. **PM 與狀態準備** — 驗證／對應在 GitHub Project Board 中的 Issue 狀態。
2. **產出原始碼 by CrewAI** — 產出 `.n8n/hk-building-biography-workflow.json`（n8n 工作流 JSON）及 `.crewai/`（Agent、Tasks、Tools 及設定檔）。
3. **產出文檔 by CrewAI** — 產出 `toc.md`、`docs/*.md`（完整集合）、`README.md`。
4. **更新 CHANGELOG** — 追加紀錄，依變更級別調升版號。
5. **即時版本控制與推送** — stage 產出，提交，推送至 `origin/dev-001`。
6. **PM 狀態同步** — 更新 GitHub Project／Issue 狀態為完成。

## n8n 工作流：每座建築物的原子化執行迴圈（6 步驟，依序執行）

n8n 工作流為生產階段，於提示詞工作流產出成熟後啟動。每座建築物以原子化方式處理；單座建築物失敗不得中斷整體迴圈。

1. **PM 與狀態準備** — 驗證／對應該建築物在 GitHub Project Board 中的 Issue 狀態。
2. **CrewAI 研究與硬關卡** — 先執行 Archival Researcher（歷史研究），再執行 Credibility Assessor（真實性 Hard Gate）。失敗時最多嘗試 **5 次**（1 次初試 + 4 次重試）；若仍未通過則執行 `fail-then-skip-building` — 於 `runs/{building_id}/` 記錄 Exception Log，跳過後續步驟進入下一迴圈。
3. **產出導賞手冊與文檔** — 寫入正確的分類路徑（法定古蹟 / 新界 / 市區）；更新 `docs/`。
4. **更新 CHANGELOG** — 追加紀錄，依變更級別調升版號。
5. **即時版本控制與推送** — 僅 stage 該建築物的產出，提交，推送至 `origin/dev-001`。
6. **PM 狀態同步** — 更新 GitHub Project／Issue 狀態為完成。

## 可觀測性（強制要求，非可選）

- 配置 CrewAI `step_callback` 與 `task_callback` 捕捉中間思考／對話。
- 將中間結構化狀態寫入 `.crewai/runs/{building_id}/intermediate_research.json`（建築物迭代）；提示詞工作流寫入 `.crewai/runs/prompt-workflow/intermediate_state.json`。
- n8n 即時擷取 Python 腳本經由 `stdout` 輸出的 Agent 對話／思考日誌，隨後載入 runs JSON 供狀態檢視與條件判斷。

## n8n 工作流節點（`.n8n/hk-building-biography-workflow.json`）

n8n 為**自架 Docker 容器（永久免費 Community edition，非 n8n Cloud）** — 以 `docker-compose.yml` + 自建 `Dockerfile`（含 Python + CrewAI 依賴）編排；綁定 `0.0.0.0:45678` 對外暴露，Webhook 觸發器需要可達的主機；無 Cloud 排程功能。

觸發（Webhook／外部）→ 資料讀取（讀取 建築矩陣.md / CSV/JSON）→ 迭代循環（逐建築物 Loop）→ 執行與監控（Execute Command → Python CrewAI 腳本；擷取 stdout；載入 runs JSON）。

## GitHub Actions（`.github/workflows/gh-pipeline.yml`）

單一統合檔案，三大職責：

- **自動分支推進：** push 至 `dev-001` 觸發依序合併 `dev-001 -> dev -> main`。
- **排程與手動觸發：** `workflow_dispatch` + cron `0 9 * * *`（HKT 17:00）；於 `main` 分支執行品質檢查與構建。
- **品質閘門 → 構建與部署：** 於 `main` 執行 CodeQL + SonarQube 掃描（要求零重大漏洞）；通過後 mdBook 編譯靜態文檔網站並部署。
- **PM 最終審查：** 流水線結束後同步 GitHub Project 看板與 Issue 狀態，確保全流程閉環。

## 文件引用鏈（Codebase 層）

- 專案目錄樹 → [`toc.md`](toc.md) → [`docs/*.md`](docs/)
- 專案內容 → [`DESCRIPTION`](../DESCRIPTION), [`CHANGELOG`](../CHANGELOG)
- 上層治理 → [`../AGENTS.md`](../AGENTS.md)
- n8n 工作流程 → [`.n8n/hk-building-biography-workflow.json`](.n8n/hk-building-biography-workflow.json)
- CI/CD 管線 → [`.github/workflows/gh-pipeline.yml`](../.github/workflows/gh-pipeline.yml)