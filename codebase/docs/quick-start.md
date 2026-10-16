# 快速開始

本文件引導您快速啟動「香港建築物導賞手冊自動化流水線」，從前置條件到觸發首次建築物迭代。如需完整細節，請參閱 [部署指南](deployment.md) 與 [配置說明](configurations.md)。

## 前置條件

開始前請確認以下項目已就緒：

- Docker Engine ≥ 20.10 與 Docker Compose ≥ 2.0 已安裝。
- 主機埠 `45678` 可對外存取（供 Webhook 觸發）。
- OpenAI API 金鑰（具 `gpt-4o` 存取權限）。
- 搜尋 API 金鑰（檔案研究用）。
- GitHub Personal Access Token（權限：`repo`、`project`、`workflow`）。
- 本儲存庫已複製至部署主機，且分支 `dev-001`、`dev`、`main` 存在。

如尚未安裝 Docker，請參考官方文件安裝 Docker Engine 與 Docker Compose plugin。

## 複製專案

```bash
git clone <儲存庫 URL> hk-tour-guide-n8n
cd hk-tour-guide-n8n
git checkout dev-001
```

確認專案結構包含以下關鍵檔案：

- `codebase/建築矩陣.md` — 建築物清單輸入。
- `codebase/.crewai/` — CrewAI 設定（agents.yaml、tasks.yaml、config.yaml、tools/、requirements.txt）。
- `codebase/.n8n/hk-building-biography-workflow.json` — n8n 工作流。
- `docker-compose.yml` — Docker 編排。
- `Dockerfile` — 自建映像檔（含 Python、CrewAI、gh CLI）。
- `.env.example` — 環境變數範本。

## Docker 啟動

### 建立環境變數檔

```bash
cp .env.example .env
```

編輯 `.env`，至少填入以下值（替換範本預設值）：

- `N8N_BASIC_AUTH_PASSWORD` — 設為強密碼。
- `OPENAI_API_KEY` — 您的 OpenAI 金鑰。
- `GITHUB_TOKEN` — 您的 GitHub PAT。
- `SEARCH_API_KEY` — 您的搜尋 API 金鑰。
- `WEBHOOK_URL` — 改為可達主機 URL，如 `http://{主機IP}:45678/webhook`。

### 建置與啟動

```bash
docker compose build
docker compose up -d
```

建置過程會安裝 Python、CrewAI 依賴與 GitHub CLI 至 n8n 映像檔。啟動後驗證容器運行：

```bash
docker compose ps
```

### 存取 n8n Web UI

瀏覽器開啟 `http://{主機IP}:45678`，以 `.env` 中的 Basic Auth 帳密登入。首次可能需設定擁有者帳號。

## 匯入工作流

1. 於 n8n Web UI 選擇「Workflows」→「Import from File」。
2. 匯入 `codebase/.n8n/hk-building-biography-workflow.json`。
3. 檢查節點設定：
   - **Webhook** — `POST /hk-building-tour`，Basic Auth。
   - **Read File** — `/data/codebase/建築矩陣.md`。
   - **Execute Command** — `python /data/codebase/.crewai/crew.py --building-id={{ $json.id }}`，`continueOnFail: true`。
   - **Read JSON** — `/data/codebase/.crewai/runs/{{ $json.id }}/intermediate_research.json`。
   - **If** — `{{ $json.review.verdict === 'passed' }}`。
4. 於右上角切換工作流為「Active」。

## 觸發 Webhook

### 單座建築物測試

以單座建築物觸發，驗證全流程：

```bash
curl -X POST "http://{主機IP}:45678/webhook/hk-building-tour" \
  -u "${N8N_BASIC_AUTH_USER}:${N8N_BASIC_AUTH_PASSWORD}" \
  -H "Content-Type: application/json" \
  -d '{"mode":"single","building_id":"00001"}'
```

預期回應：

```json
{"status":"accepted","execution_id":"1234","mode":"single","building_id":"00001"}
```

### 觀察執行

於 n8n「Executions」頁面觀察執行進度。正常流程為：

1. Webhook 接收請求。
2. 讀取建築矩陣，定位建築物 `00001`。
3. Execute Command 呼叫 `crew.py`。
4. `archival_researcher` 執行歷史研究。
5. `credibility_assessor` 執行硬關卡審查。
6. 通過則 `documentation_writer` 撰寫 Markdown。
7. `pm_agent` 同步 GitHub Issue 與 Project 看板。
8. 更新 CHANGELOG，提交並推送至 `dev-001`。

### 批量執行（進階）

單座驗證通過後，以批量模式觸發：

```bash
curl -X POST "http://{主機IP}:45678/webhook/hk-building-tour" \
  -u "${N8N_BASIC_AUTH_USER}:${N8N_BASIC_AUTH_PASSWORD}" \
  -H "Content-Type: application/json" \
  -d '{"mode":"batch","category":"法定古蹟","limit":10}'
```

## 查看結果

### 導賞手冊

確認產出檔案已寫入對應分類目錄：

```bash
ls codebase/導賞手冊/法定古蹟/
```

檔名格式：`{編號}-{中文名稱}-{中文地址}.md`。

### 中介狀態

確認 `intermediate_research.json` 已產生：

```bash
ls codebase/.crewai/runs/00001/
cat codebase/.crewai/runs/00001/intermediate_research.json
```

檢查 `status` 應為 `passed`，`review.verdict` 為 `passed`，`review.confidence_score` 為 0-100。

### CHANGELOG

確認 CHANGELOG 已追加紀錄並調升版號：

```bash
cat CHANGELOG
```

### Git 提交

確認 `dev-001` 出現新提交：

```bash
git log --oneline dev-001 -5
```

提交訊息應為 `feat(building): add biography and tour guide for {中文名稱}`。

### CI/CD 部署

推送至 `dev-001` 後，GitHub Actions 自動合併至 `dev` 再至 `main`，並於 `main` 執行品質掃描。通過後 mdBook 編譯靜態網站並部署。於 GitHub Actions 頁面查看流水線執行狀態，並存取部署的靜態網站瀏覽導賞手冊。

## 下一步

- 閱讀 [部署指南](deployment.md) 了解完整部署細節與疑難排解。
- 閱讀 [配置說明](configurations.md) 調校環境變數與設定。
- 閱讀 [系統設定](settings.md) 了解 LLM 與重試參數調校。
- 閱讀 [API 文件](api.md) 了解 Webhook 與 CrewAI CLI 介面。
- 閱讀 [變更管理](crm.md) 了解分支策略與提交規範。
