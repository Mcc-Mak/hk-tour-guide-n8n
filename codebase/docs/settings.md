# 系統設定

本文件說明「香港建築物導賞手冊自動化流水線」的系統設定，涵蓋 n8n 系統設定、LLM 提供者設定、重試參數、路徑對應與時區設定。本文件與 [配置說明](configurations.md) 互補：後者著重環境變數清單，本文件著重設定值調校建議與影響。

## n8n 系統設定

### 基本認證

n8n 啟用 Basic Auth 以保護 Web UI 與 Webhook。認證由環境變數 `N8N_BASIC_AUTH_USER` 與 `N8N_BASIC_AUTH_PASSWORD` 控制。部署時必須將預設密碼 `changeme` 變更為強密碼（建議至少 16 字元，含大小寫、數字、符號）。

### 監聽與連接埠

| 設定 | 值 | 說明 |
| --- | --- | --- |
| `N8N_HOST` | `0.0.0.0` | 監聽所有介面 |
| `N8N_PORT` | `5678` | 容器內監聽埠 |
| 主機埠 | `45678` | 對外暴露埠（docker-compose 對應） |
| `N8N_PROTOCOL` | `http` | 協定（如需 HTTPS 由反向代理處理） |

### Webhook URL

`WEBHOOK_URL` 決定 n8n 對外公告的 Webhook 基底 URL。本專案預設 `http://0.0.0.0:45678/webhook`。生產部署應改為可達主機的完整 URL，如 `https://n8n.example.com/webhook`。Webhook 觸發器需要可達的主機，否則外部系統無法觸發流水線。

### 安全 Cookie

本專案以 HTTP（無 TLS）部署並以 IP 存取，因此 `N8N_SECURE_COOKIE=false` 為必要設定，否則瀏覽器（尤其是 Safari）會顯示「secure cookie」警告並可能無法登入。若改為 TLS／HTTPS 部署，應將 `N8N_SECURE_COOKIE` 設回 `true` 以啟用安全 Cookie。

### 持久化

n8n 內部狀態（工作流、憑證、執行記錄）持久化於 `n8n_data` volume（容器路徑 `/home/node/.n8n`）。此 volume 須定期備份，避免容器重建後遺失工作流設定。

### 重啟策略

`restart: unless-stopped` 確保容器於非人為停止時自動重啟，維持 n8n 持續可用。維護時可手動 `docker compose stop`。

### 排程限制

n8n Community Edition 自架環境不使用 n8n 內建 Cron 排程。所有排程由 GitHub Actions 的 cron（`0 9 * * *`，HKT 17:00）承擔，n8n 僅由 Webhook 觸發。此為硬性約束，確保觸發器分離。

## LLM 提供者設定

本專案使用兩個自架 LLM 模型，透過 HKO LiteLLM Proxy（OpenAI 兼容端點）存取，共用同一把 `HKO_API_KEY`。

### 模型清單

| 環境變數 | 模型 | 用途 |
| --- | --- | --- |
| `HKO_LLM_PRIMARY` | `zai-org/GLM-5.2-FP8` | CrewAI 團隊主力模型（第 1–3 次嘗試） |
| `HKO_LLM_FALLBACK` | `deepseek-ai/DeepSeek-V4-Flash-0731-Coding` | CrewAI 第 4–5 次重試、格式修復、所有非 CrewAI 提示 |

### 模型切換策略（CrewAI 重試迴圈）

| 嘗試次數 | 模型 | 說明 |
| --- | --- | --- |
| 第 1 次 | `zai-org/GLM-5.2-FP8` | 主力模型，首次研究與硬關卡審查 |
| 第 2 次 | `zai-org/GLM-5.2-FP8` | 主力模型重試 |
| 第 3 次 | `zai-org/GLM-5.2-FP8` | 主力模型重試 |
| 第 4 次 | `deepseek-ai/DeepSeek-V4-Flash-0731-Coding` | 回退模型，更換模型以突破僵局 |
| 第 5 次 | `deepseek-ai/DeepSeek-V4-Flash-0731-Coding` | 回退模型，最後嘗試 |

每次嘗試以單一模型跑完整個 Crew 流程，**嚴禁中途更換模型**。模型切換只發生在第 4、5 次嘗試的**開頭**。所有嘗試執行**相同的 Crew 流程**（同一批 Agent／Task，僅模型不同），不因嘗試次數而漂移目的。任一次嘗試通過硬關卡即**立即成功收尾並停止後續嘗試**（短截），例如第 1 次成功即跳過第 2–5 次。由 `config.yaml` 的 `retry.max_attempts: 5` 與 `retry.fallback_from_attempt: 4` 控制。五次仍未通過則執行 `fail-then-skip-building`。

### 非 CrewAI 提示

所有 CrewAI 團隊以外的 LLM 呼叫均使用 `HKO_LLM_FALLBACK`（`deepseek-ai/DeepSeek-V4-Flash-0731-Coding`）：

- **格式修復（Format Fixer）** — 硬關卡通過後，對產出的 Markdown 執行格式修復。僅修復格式問題（標題層級、列表縮排、表格對齊、空行、連結語法、表格欄位漂移等），**嚴禁新增、刪除或修改任何內容**。使用 `temperature: 0` 確保一致性。透過 `openai` Python 函式庫直接呼叫，不經過 CrewAI。

### 溫度與 token

| 設定 | 值 | 說明 |
| --- | --- | --- |
| `LLM_TEMPERATURE` | `0.7` | CrewAI 研究與撰寫適度發散 |
| `LLM_MAX_TOKENS` | `4096` | 確保研究報告與手冊完整輸出 |
| `format_fixer.temperature` | `0` | 格式修復使用零溫度以確保一致性 |

### 速率限制

`config.yaml` 的 `max_rpm: 10` 限制每分鐘最大 LLM 呼叫數，避免觸發 API 速率限制與成本超支。此設定與 LiteLLM Proxy 的配額須協調。

### 金鑰管理

`HKO_API_KEY` 透過 `.env` 注入容器，兩個模型共用同一把金鑰。嚴禁寫入程式碼或提交至儲存庫。CI/CD 環境以 GitHub Actions Secrets 注入。金鑰應定期輪換，並監控用量。

## 重試參數

### 硬關卡重試

`config.yaml` 的 `retry` 區塊定義硬關卡審查的重試策略：

| 設定 | 值 | 說明 |
| --- | --- | --- |
| `max_attempts` | `5` | 硬關卡最多嘗試五次 |
| `backoff_seconds` | `5` | 每次重試間退避 5 秒 |
| `fallback_from_attempt` | `4` | 第 4 次起切換至 `HKO_LLM_FALLBACK` |

五次仍未通過則執行 `fail-then-skip-building`，記錄 Exception Log 並跳過該建築物。重試上限不應過高，以免單座建築物阻塞整體進度並增加 LLM 成本。

### n8n 節點失敗處理

n8n `Execute Command` 節點設定 `continueOnFail: true`，確保單座建築物失敗不中斷 Loop。結束碼對應：

| 結束碼 | n8n 處理 |
| --- | --- |
| 0 | 成功，繼續後續節點 |
| 1 | 跳過（硬關卡未通過），標記 `skipped`，繼續下一座 |
| 2 | 輸入錯誤，記錄後繼續下一座 |
| 3 | 嚴重錯誤，記錄後依策略決定是否重排 |

### 重試調校建議

- 若大量建築物因 LLM 隨機性未通過，可提高 `max_attempts` 至 4-5，但需權衡成本。
- 若搜尋 API 配額不足，降低 `max_attempts` 並增加 `backoff_seconds`。
- 審查階段可考慮降低 `LLM_TEMPERATURE` 以提升判定一致性。

## 路徑對應

### 主機與容器路徑

`docker-compose.yml` 將 `./codebase` 掛載至容器 `/data/codebase`，確保 n8n 與 CrewAI 共用同一份檔案。所有路徑設定須使用容器內路徑。

| 用途 | 容器路徑 |
| --- | --- |
| 建築矩陣 | `/data/codebase/建築矩陣.md` |
| CrewAI 設定 | `/data/codebase/.crewai/` |
| crew.py 入口 | `/data/codebase/.crewai/crew.py` |
| runs 目錄 | `/data/codebase/.crewai/runs/` |
| 導賞手冊產出 | `/data/codebase/導賞手冊/` |
| n8n 工作流 JSON | `/data/codebase/.n8n/hk-building-biography-workflow.json` |

### 輸出路徑分類路由

`file_writer` 工具依建築物 `分類` 決定輸出子目錄：

| 分類 | 輸出目錄 |
| --- | --- |
| 法定古蹟 | `/data/codebase/導賞手冊/法定古蹟/` |
| 新界 | `/data/codebase/導賞手冊/建築/新界/` |
| 市區 | `/data/codebase/導賞手冊/建築/市區/` |

檔名格式：`{編號}-{中文名稱}-{中文地址}.md`。

### intermediate_path

`config.yaml` 的 `output.intermediate_path` 設為 `codebase/.crewai/runs`，為相對路徑。實際執行時由 `crew.py` 解析為絕對路徑（容器內 `/data/codebase/.crewai/runs`）。

## 時區設定

### n8n 時區

`docker-compose.yml` 設定 `GENERIC_TIMEZONE=Asia/Hong_Kong`，確保 n8n 時間戳以 HKT 為準。此設定影響執行記錄的時間顯示與任何時間相關判斷。

### GitHub Actions 排程時區

GHA cron `0 9 * * *` 為 UTC 時間，對應 HKT 17:00（UTC+8）。此排程於 `main` 分支執行品質檢查與構建，不在 n8n 中設定。

### JSON 時間戳

`intermediate_research.json` 的時間欄位（`started_at`、`updated_at`、`generated_at`、`ts`）採 ISO8601 格式，建議以 HKT 或 UTC 標示。為避免混淆，所有時間戳建議包含時區偏移（如 `2024-10-14T17:00:00+08:00`）。

### 時區一致性檢查

部署後請確認以下時間一致：

1. n8n 執行記錄時間為 HKT。
2. `intermediate_research.json` 時間戳正確。
3. CHANGELOG 日期與實際提交時間一致。
4. GHA cron 觸發時間為 HKT 17:00。

若時區不一致，可能導致執行記錄順序混亂或排程誤差。確認主機系統時區亦為 `Asia/Hong_Kong`（`timedatectl set-timezone Asia/Hong_Kong`），以確保容器內日期指令與日誌一致。
