# hk-tour-guide-n8n

香港建築物導賞手冊自動化流水線 — 以 CrewAI 執行歷史研究與真實性硬關卡審查，透過 n8n 工作流引擎編排每座建築物的原子化迭代迴圈，並以 mdBook 編譯及發佈靜態文檔網站，全流程由 GitHub Actions CI/CD 流水線統一管控。

> 本專案為全新專案，採用 MIT 授權條款。所有文檔與導賞手冊內容以繁體中文撰寫。

## 專案內容

- [DESCRIPTION](DESCRIPTION) — 專案簡介與定位。
- [CHANGELOG](CHANGELOG) — 依語意化版本號記錄所有顯著變更。
- [AGENTS.md](AGENTS.md) — Workflow-1（啟動階段）基礎設施治理。
- [codebase/AGENTS.md](codebase/AGENTS.md) — Workflow-2（專案階段）專案治理。
- [LICENSE](LICENSE) — MIT 授權條款。

## 架構概覽

本專案為一套**遞迴代理沙盒（Recursive Agentic Sandbox, RAS）**，於單一統合 GitHub 儲存庫中進行邏輯分離：

- **Workflow-1（啟動階段，Root）：** 由 `AGENTS.md` 治理，建置容器化 n8n + CrewAI 沙盒。
- **Workflow-2（專案階段，Codebase）：** 由 `codebase/AGENTS.md` 治理，於沙盒內執行香港建築物導賞手冊流水線。

兩階段皆受 GitHub 分支管線管控，遵循固定分支流動 `dev-001 → dev → main`。

### 第一階段：提示詞工作流（Prompt Workflow）

專案鷹架階段，由 CrewAI 產出 n8n 工作流 JSON、`.crewai/` 設定（agents、tasks、tools、config）與完整文檔集。產出成熟後方可安裝 n8n 並啟動建築物迭代迴圈。六步驟：PM 與狀態準備 → 產出原始碼 → 產出文檔 → 更新 CHANGELOG → 版本控制與推送至 `dev-001` → PM 狀態同步。

### 第二階段：n8n 工作流（建築物迭代迴圈）

生產階段，每座建築物以原子化方式處理，單座失敗不中斷整體迴圈。n8n 僅由 Webhook 觸發，Cron 排程屬於 GitHub Actions。六步驟：PM 與狀態準備 → CrewAI 研究與硬關卡（失敗最多嘗試五次，1 次初試 + 4 次重試，仍未通過則 `fail-then-skip-building`）→ 產出導賞手冊 → 更新 CHANGELOG → 版本控制與推送至 `dev-001` → PM 狀態同步。

### 核心硬性約束

- **CrewAI 為強制要求**，嚴禁以自定義手寫 Agent 取代。
- **觸發器分離** — n8n 僅由 Webhook 觸發；Cron 排程屬於 GitHub Actions（`0 9 * * *`，HKT 17:00）。
- **分支流動固定** `dev-001 → dev → main`，嚴禁直接推送至 `dev`／`main`。
- **硬關卡審查** — 無來源陳述一律不通過，五次未通過（1 次初試 + 4 次重試）則跳過並記錄。

## 快速開始

請參閱 [快速開始](codebase/docs/quick-start.md) 了解從 Docker 啟動到觸發首次建築物迭代的完整流程。完整部署細節請參閱 [部署指南](codebase/docs/deployment.md)。

```bash
cp .env.example .env        # 填入金鑰
docker compose build
docker compose up -d        # 啟動 n8n
```

n8n Web UI 與 Webhook 透過 `http://{主機IP}:45678` 存取。

## 建築矩陣

[建築矩陣](codebase/建築矩陣.md) 為流水線的輸入來源，合併市區、新界與法定古蹟三大來源，去重後收錄建築物清單。導賞手冊依分類輸出至：

- `codebase/導賞手冊/法定古蹟/{編號}-{中文名稱}-{中文地址}.md`
- `codebase/導賞手冊/建築/新界/{編號}-{中文名稱}-{中文地址}.md`
- `codebase/導賞手冊/建築/市區/{編號}-{中文名稱}-{中文地址}.md`

## 目錄樹與文檔集

[目錄樹](codebase/toc.md) 為 mdBook 風格的 SUMMARY，連結至完整文檔集：

- [專案章程](codebase/docs/charter.md)
- [使用者故事](codebase/docs/user-stories.md)
- [軟體需求規格書](codebase/docs/srs.md)
- [產品需求文件](codebase/docs/prd.md)
- [產品設計文件](codebase/docs/pdr.md)
- [架構決策記錄](codebase/docs/adr.md)
- [API 文件](codebase/docs/api.md)
- [資料結構](codebase/docs/schema.md)
- [工程設計記錄](codebase/docs/edr.md)
- [配置說明](codebase/docs/configurations.md)
- [部署指南](codebase/docs/deployment.md)
- [系統設定](codebase/docs/settings.md)
- [需求追溯矩陣](codebase/docs/rtm.md)
- [變更管理](codebase/docs/crm.md)

## n8n 工作流程

n8n 工作流定義於 [codebase/.n8n/hk-building-biography-workflow.json](codebase/.n8n/hk-building-biography-workflow.json)，包含 Webhook 觸發、建築矩陣讀取、逐建築物 Loop 迭代、Execute Command 呼叫 Python CrewAI 腳本、runs JSON 載入與條件判斷等節點。n8n 為自架 Docker Community Edition，綁定 `0.0.0.0:45678` 對外暴露。

## Docker 基礎設施

- [docker-compose.yml](docker-compose.yml) — n8n 容器編排，主機埠 `45678` 對應容器 `5678`，掛載 `./codebase` 至 `/data/codebase`。
- [Dockerfile](Dockerfile) — 自建映像檔，以 `n8nio/n8n:latest` 為基礎，安裝 Python、CrewAI 依賴與 GitHub CLI。
- [.env.example](.env.example) — 環境變數範本（n8n Basic Auth、LLM、GitHub、搜尋 API）。

## CrewAI 設定

CrewAI 設定位於 `codebase/.crewai/`：

- `agents.yaml` — 四代理：歷史檔案研究員、可信性評估員、導賞手冊撰寫員、專案經理。
- `tasks.yaml` — 研究、硬關卡審查、手冊撰寫、PM 同步四任務。
- `config.yaml` — 循序執行、`max_rpm: 10`、重試上限 3、退避 5 秒。
- `tools/` — `web_search`、`file_writer`、`git_ops` 三工具。
- `runs/` — 每次迭代的中介狀態與日誌（含 `intermediate_research.json`）。

## CI/CD 管線

單一統合流水線 [`.github/workflows/gh-pipeline.yml`](.github/workflows/gh-pipeline.yml)，三大職責：

1. **自動分支推進** — push 至 `dev-001` 觸發依序合併 `dev-001 → dev → main`。
2. **排程與手動觸發** — `workflow_dispatch` + cron `0 9 * * *`（HKT 17:00），於 `main` 執行品質檢查與構建。
3. **品質閘門 → 構建與部署** — CodeQL + SonarQube 掃描（零重大漏洞），通過後 mdBook 編譯靜態文檔網站並部署。

## 檔案結構

```
hk-tour-guide-n8n/
├── .github/workflows/gh-pipeline.yml      # GHA 統合流水線
├── docs/                                   # 根（W1）基礎設施文檔
│   ├── charter.md
│   ├── srs.md
│   └── crm.md
├── toc.md                                  # 根索引（W1）
├── codebase/                               # 專案實作（W2）
│   ├── AGENTS.md                           # Workflow-2 專案治理
│   ├── 建築矩陣.md                          # 建築物清單（輸入來源）
│   ├── toc.md                              # 專案目錄樹
│   ├── docs/                               # 完整文檔集（14 份）
│   ├── .crewai/                            # CrewAI 設定、工具、runs
│   │   ├── agents.yaml
│   │   ├── tasks.yaml
│   │   ├── config.yaml
│   │   ├── requirements.txt
│   │   ├── tools/
│   │   └── runs/{building_id}/             # 中介狀態與日誌
│   ├── .n8n/
│   │   └── hk-building-biography-workflow.json
│   ├── site/                               # mdBook 輸出
│   │   ├── book.toml
│   │   └── SUMMARY.md
│   └── 導賞手冊/
│       ├── 法定古蹟/
│       └── 建築/{新界,市區}/
├── docker-compose.yml                      # n8n 容器編排
├── Dockerfile                              # 自建映像檔
├── .env.example                            # 環境變數範本
├── AGENTS.md                               # Workflow-1 基礎設施治理
├── DESCRIPTION                             # 專案簡介
├── CHANGELOG                               # 變更記錄
├── README.md                               # 本檔
└── LICENSE                                 # MIT
```

## 授權

本專案採用 [MIT 授權條款](LICENSE)。
