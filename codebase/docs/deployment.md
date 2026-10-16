# 部署指南

本文件指引「香港建築物導賞手冊自動化流水線」的完整部署流程，涵蓋前置條件、Docker 環境建置、n8n 啟動、工作流匯入、Webhook 設定、首次執行與疑難排解。

## 前置條件

### 系統需求

- Linux 主機（建議 Ubuntu 22.04 或同等），具備 root 或 sudo 權限。
- 至少 2 GB 記憶體與 10 GB 磁碟空間。
- 主機埠 `45678` 開放對外存取（供 Webhook 觸發）。
- 穩定的對外網路（供 LLM API、搜尋 API、GitHub API 連線）。

### 軟體需求

- Docker Engine ≥ 20.10
- Docker Compose ≥ 2.0
- Git
- GitHub CLI（`gh`）— 已內建於自建映像檔，主機端可選

### 帳號與金鑰

- OpenAI API 金鑰（具備 `gpt-4o` 存取權限）。
- 搜尋 API 金鑰（用於檔案研究）。
- GitHub Personal Access Token（PAT），權限範圍：`repo`、`project`、`workflow`。
- GitHub 儲存庫與 Project Board 已建立。
- n8n Basic Auth 帳密（自訂強密碼）。

### 儲存庫準備

1. Fork 或複製本儲存庫至部署主機。
2. 確認分支 `dev-001`、`dev`、`main` 存在。
3. 確認 `.github/workflows/gh-pipeline.yml` 已就位。
4. 確認 `codebase/建築矩陣.md` 存在且可讀。

## Docker 環境建置

### 建立環境變數檔

複製範本並填入實際值：

```bash
cp .env.example .env
```

編輯 `.env`，填入：

- `N8N_BASIC_AUTH_USER` / `N8N_BASIC_AUTH_PASSWORD`（強密碼）
- `OPENAI_API_KEY`
- `LLM_MODEL`（預設 `gpt-4o`）
- `GITHUB_TOKEN`
- `SEARCH_API_KEY`
- `WEBHOOK_URL`（改為可達主機，如 `http://{主機IP}:45678/webhook`）

### 建置自建映像檔

自建 Dockerfile 以 `n8nio/n8n:latest` 為基礎，安裝 Python、CrewAI 依賴與 GitHub CLI：

```bash
docker compose build
```

建置過程會：
1. 安裝 `python3`、`py3-pip`、`git`。
2. 下載並安裝 GitHub CLI v2.44.1。
3. 複製 `codebase/.crewai/requirements.txt` 並 `pip3 install` CrewAI 依賴。
4. 以 `node` 使用者執行 n8n。

### 驗證建置

```bash
docker compose config
```

確認服務、連接埠、Volume 掛載與環境變數正確無誤。

## n8n 啟動

```bash
docker compose up -d
```

啟動後驗證：

```bash
docker compose ps
docker compose logs -f n8n
```

### 存取 Web UI

瀏覽器開啟 `http://{主機IP}:45678`，以 `.env` 中的 Basic Auth 帳密登入。首次登入可能需設定擁有者帳號（依 n8n 版本而定）。

### 時區確認

確認 n8n 時區為 `Asia/Hong_Kong`（HKT）。此設定由 `docker-compose.yml` 的 `GENERIC_TIMEZONE` 注入，確保時間戳與排程一致。

## 匯入工作流

1. 於 n8n Web UI 左側選單選擇「Workflows」。
2. 點選「Import from File」。
3. 選擇 `codebase/.n8n/hk-building-biography-workflow.json`（容器內路徑 `/data/codebase/.n8n/hk-building-biography-workflow.json`，或自主機上傳）。
4. 匯入後檢查所有節點連線與設定。

### 節點設定檢查

- **Webhook 節點** — HTTP Method: `POST`，Path: `hk-building-tour`，Authentication: Basic Auth。
- **Read File 節點** — 路徑 `/data/codebase/建築矩陣.md`。
- **Loop 節點** — 逐建築物迭代。
- **Execute Command 節點** — 指令 `python /data/codebase/.crewai/crew.py --building-id={{ $json.id }}`，`continueOnFail: true`。
- **Read JSON 節點** — 路徑 `/data/codebase/.crewai/runs/{{ $json.id }}/intermediate_research.json`。
- **If 節點** — 條件 `{{ $json.review.verdict === 'passed' }}`。

### 啟用工作流

於工作流頁面右上角切換為「Active」。Webhook 端點隨即生效。

## Webhook 設定

### Webhook URL

完整 Webhook URL 為：

```
http://{主機IP}:45678/webhook/hk-building-tour
```

此 URL 須與 `.env` 的 `WEBHOOK_URL` 一致。

### 可達性測試

```bash
curl -X POST "http://{主機IP}:45678/webhook/hk-building-tour" \
  -u "${N8N_BASIC_AUTH_USER}:${N8N_BASIC_AUTH_PASSWORD}" \
  -H "Content-Type: application/json" \
  -d '{"mode":"single","building_id":"00001"}'
```

預期回應 `200 OK` 與 `accepted` 狀態。

### 反向代理（可選）

如需 HTTPS 或網域，於主機前端架設 Nginx/Caddy 反向代理，將外部 HTTPS 轉發至 `localhost:45678`，並更新 `WEBHOOK_URL` 為 HTTPS 網址。

## 首次執行

### 單座建築物測試

以單座建築物觸發，驗證全流程閉環：

1. 觸發 Webhook（如上節 curl 指令）。
2. 於 n8n「Executions」頁面觀察執行進度。
3. 確認 `crew.py` 執行：研究 → 硬關卡審查 → 撰寫手冊 → PM 同步。
4. 確認產出檔案：`codebase/導賞手冊/{分類}/{編號}-{名稱}-{地址}.md`。
5. 確認中介狀態：`codebase/.crewai/runs/{編號}/intermediate_research.json`。
6. 確認 CHANGELOG 已更新。
7. 確認 `dev-001` 出現新提交。

### 批量執行

單座驗證通過後，以批量模式觸發：

```bash
curl -X POST "http://{主機IP}:45678/webhook/hk-building-tour" \
  -u "${N8N_BASIC_AUTH_USER}:${N8N_BASIC_AUTH_PASSWORD}" \
  -H "Content-Type: application/json" \
  -d '{"mode":"batch","category":"法定古蹟","limit":10}'
```

觀察 Loop 迭代是否逐座完成，單座失敗是否正確跳過。

### CI/CD 驗證

1. 確認 `dev-001` 推送觸發 GHA 自動合併至 `dev` 再至 `main`。
2. 確認 `main` 上 CodeQL + SonarQube 掃描執行。
3. 確認通過品質閘門後 mdBook 編譯並部署靜態網站。
4. 確認 GitHub Project 看板與 Issue 狀態已同步。

## 疑難排解

### Webhook 無回應

- 確認 n8n 容器運行中：`docker compose ps`。
- 確認主機防火牆允許 45678 埠。
- 確認 `WEBHOOK_URL` 與實際 URL 一致。
- 確認工作流已啟用（Active）。

### Execute Command 失敗

- 確認 `crew.py` 存在於容器內 `/data/codebase/.crewai/crew.py`。
- 確認 Python 與 CrewAI 依賴已安裝：`docker compose exec n8n python -c "import crewai"`。
- 確認環境變數已注入容器：`docker compose exec n8n env | grep OPENAI`。
- 查看 `runs/{building_id}/stdout.log` 與 `exception.log`。

### 硬關卡持續失敗

- 確認 `SEARCH_API_KEY` 有效且配額充足。
- 確認搜尋 API 可達。
- 檢視 `intermediate_research.json` 的 `review.issues` 了解不通過原因。
- 該建築物將於五次未通過（1 次初試 + 4 次重試）後跳過，不影響整體流程。

### git push 失敗

- 確認 `GITHUB_TOKEN` 有效且具備 `repo` 權限。
- 確認容器內 `gh` CLI 已認證。
- 確認分支保護規則未阻擋 `dev-001` 推送。
- 確認儲存庫遠端 URL 正確。

### mdBook 未部署

- 確認 GHA 於 `main` 觸發。
- 確認品質閘門（CodeQL + SonarQube）通過，零重大漏洞。
- 確認 mdBook 已安裝於 GHA 執行環境。
- 查看 GHA 執行日誌定位失敗步驟。
