# 配置說明

本文件詳述「香港建築物導賞手冊自動化流水線」的所有配置項，涵蓋環境變數（`.env`）、n8n 設定、CrewAI 設定（`config.yaml`）、GitHub Actions Secrets 與路徑對應表。所有敏感金鑰須以環境變數或 Secrets 注入，嚴禁寫入程式碼或提交至儲存庫。

## 環境變數（.env）

`.env.example` 為環境變數範本，部署前須複製為 `.env` 並填入實際值。`.gitignore` 應排除 `.env` 以避免金鑰外洩。

### n8n Basic Auth

| 變數 | 預設值 | 說明 |
| --- | --- | --- |
| `N8N_BASIC_AUTH_USER` | `admin` | n8n Web UI 登入帳號 |
| `N8N_BASIC_AUTH_PASSWORD` | `changeme` | n8n Web UI 登入密碼（部署時必須變更） |

### n8n Network

| 變數 | 預設值 | 說明 |
| --- | --- | --- |
| `N8N_HOST` | `0.0.0.0` | n8n 監聽主機 |
| `N8N_PORT` | `5678` | 容器內監聽埠 |
| `WEBHOOK_URL` | `http://0.0.0.0:45678/webhook` | Webhook 對外基底 URL（主機埠 45678） |

### HKO LLM Provider（LiteLLM Proxy — OpenAI 兼容）

| 變數 | 預設值 | 說明 |
| --- | --- | --- |
| `HKO_API_KEY` | `your-hko-api-key-here` | HKO LiteLLM Proxy 共用 API 金鑰 |
| `HKO_LLM_BASE_URL` | `https://litellm.services.hko.gov.hk` | LiteLLM Proxy 基底 URL |
| `HKO_LLM_PRIMARY` | `zai-org/GLM-5.2-FP8` | CrewAI 主力模型（第 1–3 次嘗試） |
| `HKO_LLM_FALLBACK` | `deepseek-ai/DeepSeek-V4-Flash-0731-Coding` | CrewAI 回退模型（第 4–5 次嘗試）、格式修復、所有非 CrewAI 提示 |
| `LLM_TEMPERATURE` | `0.7` | LLM 溫度參數 |
| `LLM_MAX_TOKENS` | `4096` | LLM 最大輸出 token 數 |

### GitHub

| 變數 | 預設值 | 說明 |
| --- | --- | --- |
| `GITHUB_TOKEN` | `ghp-your-token-here` | GitHub PAT，需具備 repo、project 寫入權限 |

### CrewAI

| 變數 | 預設值 | 說明 |
| --- | --- | --- |
| `CREWAI_VERBOSE` | `true` | 啟用 CrewAI 詳細日誌 |

### Search API

| 變數 | 預設值 | 說明 |
| --- | --- | --- |
| `SEARCH_API_KEY` | `your-search-api-key` | 檔案研究用搜尋 API 金鑰 |

## n8n 設定

n8n 設定透過 `docker-compose.yml` 的 `environment` 區塊注入，並結合 `.env` 變數。

### docker-compose 環境變數

| 變數 | 值 | 說明 |
| --- | --- | --- |
| `N8N_HOST` | `0.0.0.0` | 監聽主機 |
| `N8N_PORT` | `5678` | 容器內埠 |
| `N8N_PROTOCOL` | `http` | 協定 |
| `N8N_SECURE_COOKIE` | `false` | 停用安全 Cookie（HTTP 部署必設，避免 Safari/非 localhost 存取警告） |
| `WEBHOOK_URL` | `http://0.0.0.0:45678/webhook` | Webhook 對外 URL |
| `N8N_BASIC_AUTH_ACTIVE` | `true` | 啟用 Basic Auth |
| `GENERIC_TIMEZONE` | `Asia/Hong_Kong` | 時區（HKT） |
| `N8N_BASIC_AUTH_USER` | `${N8N_BASIC_AUTH_USER}` | 取自 .env |
| `N8N_BASIC_AUTH_PASSWORD` | `${N8N_BASIC_AUTH_PASSWORD}` | 取自 .env |

### 連接埠對應

主機埠 `45678` 對應容器埠 `5678`，n8n Web UI 與 Webhook 皆透過 `http://{host}:45678` 存取。

### Volume 掛載

| Volume | 容器路徑 | 用途 |
| --- | --- | --- |
| `n8n_data` | `/home/node/.n8n` | n8n 內部狀態持久化 |
| `./codebase` | `/data/codebase` | 建築矩陣、CrewAI 設定、產出目錄 |

### 重啟策略

`restart: unless-stopped` — 容器於非人為停止時自動重啟，確保 n8n 持續可用。

## CrewAI 設定（config.yaml）

`codebase/.crewai/config.yaml` 為 CrewAI 全域設定，定義 Crew 行為、LLM 參數、輸出格式與重試策略。

### crew 區塊

| 鍵 | 值 | 說明 |
| --- | --- | --- |
| `process` | `sequential` | 循序執行任務 |
| `verbose` | `true` | 詳細日誌 |
| `memory` | `true` | 啟用代理記憶 |
| `max_rpm` | `10` | 每分鐘最大 LLM 呼叫數（限流） |

### llm 區塊

| 鍵 | 值 | 說明 |
| --- | --- | --- |
| `base_url` | `${HKO_LLM_BASE_URL:https://litellm.services.hko.gov.hk}` | LiteLLM Proxy 基底 URL |
| `primary_model` | `${HKO_LLM_PRIMARY:zai-org/GLM-5.2-FP8}` | 主力模型（第 1–3 次嘗試） |
| `fallback_model` | `${HKO_LLM_FALLBACK:deepseek-ai/DeepSeek-V4-Flash-0731-Coding}` | 回退模型（第 4–5 次嘗試） |
| `temperature` | `0.7` | 溫度 |
| `max_tokens` | `4096` | 最大輸出 token |

### format_fixer 區塊

| 鍵 | 值 | 說明 |
| --- | --- | --- |
| `model` | `${HKO_LLM_FALLBACK:deepseek-ai/DeepSeek-V4-Flash-0731-Coding}` | 格式修復用模型（非 CrewAI，直接 LLM 呼叫） |
| `temperature` | `0` | 格式修復使用零溫度以確保一致性 |
| `prompt` | （系統提示詞） | 僅修復 Markdown 格式（含表格欄位漂移），嚴禁新增／刪除／修改內容 |

### output 區塊

| 鍵 | 值 | 說明 |
| --- | --- | --- |
| `format` | `json` | 輸出格式 |
| `save_intermediate` | `true` | 保存中介狀態 |
| `intermediate_path` | `codebase/.crewai/runs` | 中介狀態目錄 |

### retry 區塊

| 鍵 | 值 | 說明 |
| --- | --- | --- |
| `max_attempts` | `5` | 硬關卡重試上限 |
| `backoff_seconds` | `5` | 重試退避秒數 |
| `fallback_from_attempt` | `4` | 第幾次嘗試起切換至回退模型 |

## GHA Secrets

GitHub Actions 流水線所需的 Secrets，於儲存庫設定中以 Encrypted Secrets 注入。

| Secret 名稱 | 用途 |
| --- | --- |
| `GITHUB_TOKEN` | 自動提供，用於合併分支與 Issue 操作 |
| `HKO_API_KEY` | CI 中執行 CrewAI（如需） |
| `SONAR_TOKEN` | SonarQube 掃描認證 |
| `DEPLOY_TOKEN` | 部署靜態網站至託管目標 |

### GHA 觸發條件

| 觸發 | 條件 | 動作 |
| --- | --- | --- |
| `push` | `dev-001` 分支 | 自動合併至 dev → main |
| `workflow_dispatch` | 手動 | 品質檢查與構建 |
| `schedule` | `0 9 * * *`（HKT 17:00） | 於 main 執行品質檢查與構建 |

## 路徑對應表

| 主機路徑 | 容器路徑 | 說明 |
| --- | --- | --- |
| `./codebase` | `/data/codebase` | 程式碼與資料根目錄 |
| `./codebase/建築矩陣.md` | `/data/codebase/建築矩陣.md` | 建築物清單輸入 |
| `./codebase/.crewai/` | `/data/codebase/.crewai/` | CrewAI 設定與腳本 |
| `./codebase/.crewai/crew.py` | `/data/codebase/.crewai/crew.py` | CrewAI 入口腳本 |
| `./codebase/.crewai/runs/` | `/data/codebase/.crewai/runs/` | 中介狀態與日誌 |
| `./codebase/導賞手冊/` | `/data/codebase/導賞手冊/` | 導賞手冊產出目錄 |
| `./codebase/.n8n/` | `/data/codebase/.n8n/` | n8n 工作流 JSON |

### n8n 節點路徑設定

- Read File 節點路徑：`/data/codebase/建築矩陣.md`
- Execute Command 節點指令：`python /data/codebase/.crewai/crew.py --building-id={{ $json.id }}`
- file_writer 寫入根目錄：`/data/codebase/導賞手冊/`
- runs 寫入根目錄：`/data/codebase/.crewai/runs/`

## 配置檢查清單

部署前請逐項確認：

1. `.env` 已建立且金鑰已填入（非範本預設值）。
2. `N8N_BASIC_AUTH_PASSWORD` 已變更為強密碼。
3. `HKO_API_KEY` 有效且有足夠配額。
4. `GITHUB_TOKEN` 具備 repo 與 project 寫入權限。
5. `SEARCH_API_KEY` 有效。
6. `GENERIC_TIMEZONE` 設為 `Asia/Hong_Kong`。
7. 主機埠 45678 可對外存取（Webhook 可達）。
8. GHA Secrets（`SONAR_TOKEN` 等）已設定。
9. 分支保護規則已啟用（禁止直接推 dev/main）。
10. `codebase/` 目錄已掛載至容器。
