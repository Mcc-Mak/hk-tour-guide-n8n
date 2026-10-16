# API 文件

本文件描述「香港建築物導賞手冊自動化流水線」的對外與內部 API 介面，涵蓋 n8n Webhook API、CrewAI CLI 介面與 GitHub CLI 操作。所有介面均以 JSON 為資料交換格式，認證採環境變數注入的金鑰或 Basic Auth。

## n8n Webhook API

### 端點

```
POST /webhook/hk-building-tour
```

n8n 自架容器綁定 `0.0.0.0:45678`（主機埠）對應容器內 `5678`。Webhook URL 由環境變數 `WEBHOOK_URL`（預設 `http://0.0.0.0:45678/webhook`）組合而成。完整 URL 為：

```
{WEBHOOK_URL}/hk-building-tour
```

### 認證

n8n 啟用 Basic Auth，認證憑證由環境變數 `N8N_BASIC_AUTH_USER` 與 `N8N_BASIC_AUTH_PASSWORD` 提供。請求須帶 `Authorization: Basic {base64(user:password)}` 標頭。

### 請求

| 欄位 | 型別 | 必填 | 說明 |
| --- | --- | --- | --- |
| `mode` | string | 否 | 觸發模式，`single`（單座）或 `batch`（批量，預設） |
| `building_id` | string | 條件必填 | `mode=single` 時指定建築物編號 |
| `category` | string | 否 | 限制分類：`法定古蹟`／`新界`／`市區` |
| `limit` | integer | 否 | 批量模式最多處理筆數 |

### 請求範例

```json
{
  "mode": "single",
  "building_id": "00001"
}
```

批量範例：

```json
{
  "mode": "batch",
  "category": "法定古蹟",
  "limit": 10
}
```

### 回應

n8n Webhook 預設回應為 `200 OK`，body 含觸發確認與執行 ID：

```json
{
  "status": "accepted",
  "execution_id": "1234",
  "mode": "single",
  "building_id": "00001"
}
```

### 錯誤碼

| HTTP 狀態 | 原因 |
| --- | --- |
| 401 | Basic Auth 認證失敗 |
| 404 | Webhook 路徑不存在（檢查 `WEBHOOK_URL` 與工作流是否啟用） |
| 500 | n8n 內部錯誤（檢查容器日誌） |

### 觸發範例（curl）

```bash
curl -X POST "http://localhost:45678/webhook/hk-building-tour" \
  -u "${N8N_BASIC_AUTH_USER}:${N8N_BASIC_AUTH_PASSWORD}" \
  -H "Content-Type: application/json" \
  -d '{"mode":"single","building_id":"00001"}'
```

## CrewAI CLI 介面

n8n 透過 `Execute Command` 節點呼叫 Python CrewAI 腳本 `crew.py`。腳本位置為 `codebase/.crewai/crew.py`（容器內掛載於 `/data/codebase/.crewai/crew.py`）。

### 指令格式

```bash
python /data/codebase/.crewai/crew.py --building-id {building_id} [--phase {research|review|write|pm}]
```

### 參數說明

| 參數 | 必填 | 說明 |
| --- | --- | --- |
| `--building-id` | 是 | 建築物五位編號（如 `00001`），對應建築矩陣 |
| `--phase` | 否 | 執行階段：`research`（研究）、`review`（硬關卡審查）、`write`（撰寫手冊）、`pm`（狀態同步）。省略則執行完整流程 |
| `--max-retries` | 否 | 硬關卡重試上限，預設 3（同 config.yaml） |
| `--verbose` | 否 | 啟用詳細日誌，預設依 `CREWAI_VERBOSE` |

### stdout 輸出契約

`crew.py` 以 stdout 輸出結構化 JSON 日誌行（每行一個 JSON 物件），供 n8n 即時擷取並載入。每筆日誌包含：

| 欄位 | 說明 |
| --- | --- |
| `ts` | ISO8601 時間戳 |
| `phase` | 階段名稱 |
| `agent` | 代理識別碼 |
| `event` | 事件類型（`step`、`task`、`verdict`、`error`） |
| `payload` | 事件內容（思考片段、任務結果、判定、錯誤訊息） |

`verdict` 事件 payload 範例：

```json
{"ts":"2024-10-14T09:00:01Z","phase":"review","agent":"credibility_assessor","event":"verdict","payload":{"verdict":"passed","confidence_score":92}}
```

### 回傳碼

| 結束碼 | 意義 |
| --- | --- |
| 0 | 流程成功完成 |
| 1 | 硬關卡五次未通過（1 次初試 + 4 次重試，已記錄 Exception Log 並跳過） |
| 2 | 輸入錯誤（如 `building_id` 不存在） |
| 3 | 嚴重錯誤（LLM API、搜尋 API 失敗等） |

n8n 依結束碼進行條件分支：結束碼 1 視為「跳過」而非失敗，繼續下一座建築物。

### 環境變數依賴

`crew.py` 讀取以下環境變數：`OPENAI_API_KEY`、`LLM_MODEL`、`LLM_TEMPERATURE`、`LLM_MAX_TOKENS`、`GITHUB_TOKEN`、`SEARCH_API_KEY`、`CREWAI_VERBOSE`。這些由 `docker-compose.yml` 注入或於 n8n 節點環境中設定。

## GitHub CLI 操作

自建 Dockerfile 已安裝 GitHub CLI（`gh` v2.44.1）。`pm_agent` 透過 `git_ops` 工具封裝以下操作。

### 認證

```bash
echo "${GITHUB_TOKEN}" | gh auth login --with-token
```

### Issue 狀態更新

```bash
gh issue close {issue_number} --repo {owner}/{repo} --comment "建築物 {building_id} 導賞手冊已完成並合併。"
```

### Project 看板同步

```bash
gh project item-edit --project {project_number} --id {item_id} --field-name "Status" --single-select-option "Done"
```

### 分支合併（由 GHA 自動執行）

```bash
git checkout dev && git merge dev-001 --no-ff && git push origin dev
git checkout main && git merge dev --no-ff && git push origin main
```

### 提交規範

每座建築物提交訊息：

```
feat(building): add biography and tour guide for {中文名稱}

- 建築物編號: {building_id}
- 分類: {法定古蹟|新界|市區}
- 通過硬關卡審查，信心分數: {score}
```

提示詞工作流提交訊息：

```
feat(scaffolding): {簡述產出內容}
```

### 提交範例

```bash
git add codebase/導賞手冊/法定古蹟/00001-前九廣鐵路鐘樓-尖沙咀.md CHANGELOG
git commit -m "feat(building): add biography and tour guide for 前九廣鐵路鐘樓" -m "..."
git push origin dev-001
```

## 錯誤處理與重試

- n8n `Execute Command` 節點設定 `continueOnFail: true`，確保單座失敗不中斷 Loop。
- 結束碼 1（跳過）記錄於 Exception Log，n8n 將該建築物標記為 `skipped` 並繼續。
- 結束碼 3（嚴重錯誤）記錄後依重試策略決定是否重新排程該座建築物。
