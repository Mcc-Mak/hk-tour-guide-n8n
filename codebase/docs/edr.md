# 工程設計記錄

本工程設計記錄（Engineering Design Record, EDR）描述「香港建築物導賞手冊自動化流水線」的實作細節、技術棧、依賴圖、建置流程與部署流程，作為工程團隊實作與維運的技術參考。

## 實作細節

### CrewAI 多代理實作

代理以聲明式 YAML 定義於 `codebase/.crewai/agents.yaml`，任務定義於 `tasks.yaml`，全域設定於 `config.yaml`。Crew 採循序（sequential）執行，依序為 `research_task` → `credibility_task` → `documentation_task` → `pm_sync_task`。

四個代理及其職責：

- `archival_researcher`（歷史檔案研究員）— 使用 `web_search` 工具，產出附來源的 JSON 研究報告。
- `credibility_assessor`（可信性評估員）— 執行硬關卡審查，無工具，僅依賴研究報告判定。
- `documentation_writer`（導賞手冊撰寫員）— 使用 `file_writer` 工具，將研究轉為 Markdown 並寫入分類路徑。
- `pm_agent`（專案經理）— 使用 `git_ops` 工具，透過 GitHub CLI 更新 Issue 與 Project 看板。

### 工具實作

工具位於 `codebase/.crewai/tools/`：

- `web_search.py` — 封裝搜尋 API，回傳結構化搜尋結果供研究員引用。
- `file_writer.py` — 依分類路徑與檔名格式寫入 Markdown，自動建立目錄。
- `git_ops.py` — 封裝 `git` 與 `gh` 指令，執行 stage、提交、推送與 Issue 同步。

### 可觀測性實作

`crew.py` 配置 `step_callback` 與 `task_callback`，將每次代理思考與任務結果以 JSON 行寫入 stdout 並同步寫入 `intermediate_research.json` 的 `steps` 陣列。n8n `Execute Command` 節點擷取 stdout 後，以 `Read JSON` 節點載入 runs JSON 進行條件判斷（如 `review.verdict` 是否為 `passed`）。

### 重試與跳過實作

硬關卡審查於 `crew.py` 中以迴圈實作，`max_attempts` 預設 5（1 次初試 + 4 次重試），每次失敗 `backoff_seconds` 5 秒。五次未通過時寫入 `exception.log`，將 `status` 設為 `skipped`，以結束碼 1 退出。n8n 以 `continueOnFail: true` 並依結束碼 1 判定為「跳過」而非「失敗」，繼續下一座建築物。

## 技術棧

### CrewAI

- `crewai>=0.70.0` — 多代理框架核心。
- `crewai-tools>=0.12.0` — 工具集（web_search 等）。
- `pyyaml>=6.0` — 解析 agents.yaml、tasks.yaml、config.yaml。
- `requests>=2.31.0` — HTTP 呼叫（搜尋 API、GitHub API）。
- `python-dotenv>=1.0.0` — 載入環境變數。

### n8n

- n8n Community Edition（`n8nio/n8n:latest` 為基礎映像）。
- 自架 Docker，以 `docker-compose.yml` 編排。
- Webhook 觸發器、Loop、Execute Command、Read File、Read JSON、If、HTTP Request 節點。

### Docker

- 基礎映像 `n8nio/n8n:latest`。
- 自建映像檔安裝 `python3`、`py3-pip`、`git`、GitHub CLI v2.44.1。
- 安裝 CrewAI 依賴（`requirements.txt`）。
- 以 `node` 使用者執行 n8n，暴露埠 `5678`。
- 主機埠 `45678` 對應容器埠 `5678`。

### mdBook

- 於 GitHub Actions 執行環境安裝 mdBook。
- 以 `codebase/toc.md` 為 SUMMARY 編譯靜態網站。
- 部署至 GitHub Pages 或同等靜態託管。

### GitHub Actions

- 單一統合檔案 `.github/workflows/gh-pipeline.yml`。
- 三大職責：自動分支推進、排程與手動觸發品質檢查、品質閘門後構建部署。
- CodeQL + SonarQube 掃描，要求零重大漏洞。

## 依賴圖

```
建築矩陣.md
   │
   ▼
n8n Webhook (觸發)
   │
   ▼
n8n Loop (逐建築物)
   │
   ├──▶ Execute Command ──▶ crew.py
   │                          │
   │                          ├──▶ archival_researcher ──▶ web_search ──▶ 搜尋 API
   │                          ├──▶ credibility_assessor (硬關卡)
   │                          ├──▶ documentation_writer ──▶ file_writer ──▶ 檔案系統
   │                          └──▶ pm_agent ──▶ git_ops ──▶ gh CLI ──▶ GitHub API
   │
   ├──▶ intermediate_research.json (狀態契約)
   │
   ├──▶ CHANGELOG 更新
   │
   └──▶ git commit + push origin dev-001
              │
              ▼
        GitHub Actions (gh-pipeline.yml)
              │
              ├──▶ 合併 dev-001 → dev → main
              ├──▶ CodeQL + SonarQube 掃描
              └──▶ mdBook 編譯 + 部署
```

### 關鍵依賴關係

- `crew.py` 依賴 `agents.yaml`、`tasks.yaml`、`config.yaml` 與 `tools/`。
- `file_writer` 依賴建築矩陣的分類路由決定輸出路徑。
- `git_ops` 依賴 `GITHUB_TOKEN` 與 `gh` CLI 已認證。
- n8n 依賴 `crew.py` 的 stdout JSON 與 runs JSON 進行條件判斷。
- GHA 依賴 `dev-001` 推送事件觸發分支推進。

## 建置流程

### 本地建置

1. 確認 Docker 與 Docker Compose 已安裝。
2. 複製 `.env.example` 為 `.env` 並填入金鑰。
3. 執行 `docker compose build` 建置自建映像檔（安裝 Python、CrewAI、gh CLI）。
4. 執行 `docker compose up -d` 啟動 n8n。
5. 存取 `http://localhost:45678` 並以 Basic Auth 登入。

### CrewAI 依賴建置

`Dockerfile` 於建置階段複製 `codebase/.crewai/requirements.txt` 並執行 `pip3 install`，確保容器內具備 `crewai`、`crewai-tools`、`pyyaml`、`requests`、`python-dotenv`。

### n8n 工作流匯入

1. 於 n8n Web UI 中選擇「Import from File」。
2. 匯入 `codebase/.n8n/hk-building-biography-workflow.json`。
3. 設定 Webhook 節點的 HTTP 方法與路徑。
4. 設定 Execute Command 節點的指令（`python /data/codebase/.crewai/crew.py --building-id={{ $json.id }}`）。
5. 啟用工作流。

## 部署流程

### 容器部署

`docker-compose.yml` 將 `./codebase` 掛載至容器 `/data/codebase`，確保 n8n 可讀取建築矩陣、CrewAI 設定與寫入產出。`n8n_data` volume 持久化 n8n 內部狀態。容器以 `restart: unless-stopped` 確保自動重啟。

### CI/CD 部署

1. 建築物產出推送至 `dev-001`。
2. GHA 觸發自動合併 `dev-001 → dev → main`。
3. 於 `main` 執行 CodeQL + SonarQube 掃描。
4. 通過品質閘門後，GHA 安裝 mdBook 並編譯 `codebase/` 為靜態網站。
5. 部署靜態網站至 GitHub Pages（或同等目標）。
6. GHA 同步 GitHub Project 看板與 Issue 狀態，確保流程閉環。

### 環境變數注入

所有金鑰（`OPENAI_API_KEY`、`GITHUB_TOKEN`、`SEARCH_API_KEY`、`N8N_BASIC_AUTH_PASSWORD`）透過 `.env` 注入 docker-compose，於容器內以環境變數形式供 `crew.py` 與 n8n 使用。CI/CD 環境則以 GitHub Actions Secrets 注入，嚴禁寫入程式碼或提交至儲存庫。

### 回滾策略

- 建築物產出以 Git 提交為單位，可透過 `git revert` 回滾單座建築物。
- `main` 分支保留完整歷史，mdBook 部署可重新觸發以重新編譯。
- n8n 工作流變更可透過工作流 JSON 的 Git 版本控制回滾。
