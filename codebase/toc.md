# 目錄

本目錄為香港建築物導賞手冊專案的 mdBook 風格目錄樹（SUMMARY.md 格式）。
所有文檔以繁體中文撰寫，並依據專案兩階段架構（提示詞工作流 + n8n 工作流）進行組織。
讀者可依下列順序閱讀，以完整理解專案的願景、需求、設計、實作與維運流程。

- [簡介](../README.md)
- [快速開始](docs/quick-start.md)
- [建築矩陣](建築矩陣.md)

# 文檔集

以下文件構成專案的完整文檔集合，涵蓋章程、需求、設計、架構決策、API、資料結構、工程記錄、配置、部署、設定、追溯矩陣與變更管理。

- [專案章程](docs/charter.md)
- [使用者故事](docs/user-stories.md)
- [軟體需求規格書](docs/srs.md)
- [產品需求文件](docs/prd.md)
- [產品設計文件](docs/pdr.md)
- [架構決策記錄](docs/adr.md)
- [API 文件](docs/api.md)
- [資料結構](docs/schema.md)
- [工程設計記錄](docs/edr.md)
- [配置說明](docs/configurations.md)
- [部署指南](docs/deployment.md)
- [系統設定](docs/settings.md)
- [需求追溯矩陣](docs/rtm.md)
- [變更管理](docs/crm.md)

# 閱讀指引

本專案採用兩階段流水線架構，建議讀者依下列路徑理解整體設計：

1. **認識專案** — 先閱讀 [簡介](../README.md) 與 [專案章程](docs/charter.md)，了解願景、使命與範圍。
2. **理解需求** — 接著閱讀 [使用者故事](docs/user-stories.md) 與 [軟體需求規格書](docs/srs.md)，掌握功能性與非功能性需求。
3. **產品規劃** — 閱讀 [產品需求文件](docs/prd.md) 與 [產品設計文件](docs/pdr.md)，理解功能清單、里程碑與架構設計。
4. **架構決策** — 閱讀 [架構決策記錄](docs/adr.md)，了解關鍵技術選型背後的理由與權衡。
5. **技術細節** — 閱讀 [API 文件](docs/api.md)、[資料結構](docs/schema.md) 與 [工程設計記錄](docs/edr.md)，掌握實作層面的契約與結構。
6. **部署與設定** — 閱讀 [配置說明](docs/configurations.md)、[部署指南](docs/deployment.md) 與 [系統設定](docs/settings.md)，完成環境建置。
7. **品質與治理** — 閱讀 [需求追溯矩陣](docs/rtm.md) 與 [變更管理](docs/crm.md)，確保需求可追溯且變更受控。
8. **實際操作** — 最後閱讀 [快速開始](docs/quick-start.md)，動手啟動專案並觸發首次建築物迭代。

# 文檔命名規範

所有文檔檔名均為小寫英文並以連字號分隔，對應 mdBook 的 SUMMARY.md 慣例：

| 檔名 | 用途 |
| --- | --- |
| `charter.md` | 專案章程，定義願景、使命、範圍與成功準則 |
| `user-stories.md` | 使用者故事，含人物誌與驗收標準 |
| `srs.md` | 軟體需求規格書，含功能性與非功能性需求 |
| `prd.md` | 產品需求文件，含功能清單與發布計畫 |
| `pdr.md` | 產品設計文件，含兩階段架構與組件設計 |
| `adr.md` | 架構決策記錄，記錄五項關鍵技術決策 |
| `api.md` | API 文件，涵蓋 n8n Webhook 與 CrewAI CLI |
| `schema.md` | 資料結構，定義建築矩陣與研究中介狀態 |
| `edr.md` | 工程設計記錄，含依賴圖與建置流程 |
| `configurations.md` | 配置說明，涵蓋環境變數與金鑰 |
| `deployment.md` | 部署指南，從 Docker 建置到首次執行 |
| `settings.md` | 系統設定，涵蓋 n8n、LLM 與時區 |
| `rtm.md` | 需求追溯矩陣，映射需求至實作與驗證 |
| `crm.md` | 變更管理，涵蓋分支策略與提交規範 |
| `quick-start.md` | 快速開始，引導使用者快速啟動專案 |

# 輸出產物路徑

除了文檔集外，本專案亦產生以下結構化產物，供流水線各階段使用：

- 建築導賞手冊：`codebase/導賞手冊/{法定古蹟,新界,市區}/{編號}-{中文名稱}-{中文地址}.md`
- CrewAI 設定：`codebase/.crewai/`（`agents.yaml`、`tasks.yaml`、`config.yaml`、`tools/`）
- n8n 工作流：`codebase/.n8n/hk-building-biography-workflow.json`
- 中介研究狀態：`codebase/.crewai/runs/{building_id}/intermediate_research.json`
- 提示詞工作流狀態：`codebase/.crewai/runs/prompt-workflow/intermediate_state.json`
- CI/CD 流水線：`.github/workflows/gh-pipeline.yml`

# 版本與維護

本目錄及所連結之文檔隨專案演進持續更新。任何文檔變更均須遵循 [變更管理](docs/crm.md) 所訂定的分支策略與提交訊息規範，並於 [CHANGELOG](../CHANGELOG) 中記錄。文檔版本號遵循語意化版本號（Semantic Versioning）。

# 文檔維護原則

- 文檔須與實作同步，任何程式碼或設定變更須同時更新對應文檔。
- 新增文檔時須於本目錄樹登錄，確保 mdBook 編譯時可正確納入導覽。
- 文檔內容以繁體中文撰寫，技術術語得保留英文原文。
- 文檔結構應層次分明，採用一致的標題層級與表格格式。
- 變更文檔時須依 [需求追溯矩陣](docs/rtm.md) 確認需求可追溯性。
- 過時文檔應標註或移除，避免誤導讀者。
