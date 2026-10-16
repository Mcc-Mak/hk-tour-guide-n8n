# 需求追溯矩陣

本需求追溯矩陣（Requirements Traceability Matrix, RTM）將「香港建築物導賞手冊自動化流水線」的每項需求映射至來源文檔、實作元件與驗證方式，確保需求可追溯、可驗證且狀態透明。

## 矩陣總覽

| 需求 ID | 需求描述 | 來源文檔 | 實作元件 | 驗證方式 | 狀態 |
| --- | --- | --- | --- | --- | --- |
| FR-001 | 建築矩陣讀取與解析 | SRS, PRD F-001 | n8n Read File 節點；`建築矩陣.md` | 觸發後 n8n 能讀取並產生 buildings 陣列 | 已實作 |
| FR-002 | CrewAI 歷史檔案研究 | SRS, PRD F-004, US-008 | `archival_researcher` 代理 + `web_search` 工具 | `intermediate_research.json` 含 research 區塊與 sources | 已實作 |
| FR-003 | 硬關卡可信度審查 | SRS, PRD F-005, ADR-005 | `credibility_assessor` 代理 | `review.verdict` 為 passed/failed 且含 confidence_score | 已實作 |
| FR-004 | 重試與跳過策略 | SRS, US-014, ADR-005 | `crew.py` 重試迴圈 + `config.yaml` retry | 五次未通過時 status=skipped 且有 exception.log | 已實作 |
| FR-005 | 導賞手冊產出 | SRS, PRD F-006, US-001 | `documentation_writer` + `file_writer` | Markdown 寫入正確分類路徑且檔名符合格式 | 已實作 |
| FR-006 | CHANGELOG 更新 | SRS, PRD F-017 | `git_ops` / n8n 節點 | CHANGELOG 追加紀錄且版號調升 | 已實作 |
| FR-007 | 版本控制與推送 | SRS, US-017, CRM | `git_ops` 工具 + GHA | 提交推送至 dev-001，訊息符合規範 | 已實作 |
| FR-008 | n8n Webhook 觸發 | SRS, PRD F-008, ADR-002 | n8n Webhook 節點 | curl 觸發回應 200 accepted | 已實作 |
| FR-009 | n8n 迭代迴圈 | SRS, PRD F-009 | n8n Loop 節點 | 批量觸發後逐座處理完成 | 已實作 |
| FR-010 | 可觀測性 | SRS, NFR-003, ADR-001 | `step_callback`/`task_callback` + runs JSON | intermediate_research.json 含 steps 陣列 | 已實作 |
| FR-011 | 專案經理狀態同步 | SRS, US-015, PRD F-007 | `pm_agent` + `git_ops` + gh CLI | GitHub Issue 關閉、Project 看板更新 | 已實作 |
| FR-012 | mdBook 部署 | SRS, PRD F-015, ADR-004 | GHA mdBook 編譯 | 靜態網站可存取且內容正確 | 規劃中 |
| FR-013 | 提示詞工作流鷹架 | SRS, PRD F-013 | CrewAI 提示詞工作流 | runs/prompt-workflow/intermediate_state.json 產生 | 已實作 |
| NFR-001 | 內容可信度（硬關卡） | SRS, Charter, ADR-005 | `credibility_assessor` 硬關卡 | 知識庫內容 100% 通過審查 | 已滿足 |
| NFR-002 | 韌性（單座失敗不中斷） | SRS, US-014 | `continueOnFail` + 跳過策略 | 單座失敗後迴圈繼續 | 已滿足 |
| NFR-003 | 可觀測性 | SRS, AGENTS.md | runs JSON + stdout 擷取 | n8n 可載入 runs JSON 進行條件判斷 | 已滿足 |
| NFR-004 | 可追溯性 | SRS, CRM | RTM + Git 提交規範 | 每筆變更可追溯至來源 | 已滿足 |
| NFR-005 | 安全性（品質閘門） | SRS, PRD F-014 | GHA CodeQL + SonarQube | main 掃描零重大漏洞 | 規劃中 |
| NFR-006 | 效能（限流） | SRS, config.yaml | `max_rpm: 10` | LLM 呼叫不超過每分鐘 10 次 | 已滿足 |
| NFR-007 | 可維護性 | SRS | YAML 聲明式配置 | 代理/任務變更無需改程式碼 | 已滿足 |
| NFR-008 | 可部署性 | SRS, ADR-002 | docker-compose 一鍵啟動 | `docker compose up` 啟動 n8n | 已滿足 |

## 需求分類追溯

### 功能性需求 → 實作元件

| 功能模組 | 需求 ID | 實作元件 |
| --- | --- | --- |
| 建築矩陣管理 | FR-001 | n8n Read File + 建築矩陣.md |
| 多代理研究 | FR-002, FR-003, FR-004 | CrewAI agents.yaml + tasks.yaml + crew.py |
| 手冊產出 | FR-005 | documentation_writer + file_writer.py |
| 工作流編排 | FR-008, FR-009, FR-010 | n8n 工作流 JSON |
| 版本控制 | FR-006, FR-007 | git_ops.py + GHA gh-pipeline.yml |
| 狀態同步 | FR-011 | pm_agent + gh CLI |
| 發佈 | FR-012 | GHA mdBook |
| 鷹架 | FR-013 | 提示詞工作流 |

### 非功能性需求 → 驗證方式

| 品質屬性 | 需求 ID | 驗證方式 |
| --- | --- | --- |
| 可信度 | NFR-001 | 抽查知識庫內容均附來源 |
| 韌性 | NFR-002 | 模擬單座失敗觀察迴圈 |
| 可觀測性 | NFR-003 | 檢視 runs JSON 與 n8n 執行畫面 |
| 可追溯性 | NFR-004 | RTM 審查 + Git log |
| 安全性 | NFR-005 | GHA 掃描報告 |
| 效能 | NFR-006 | LLM 呼叫頻率監控 |
| 可維護性 | NFR-007 | YAML 配置變更測試 |
| 可部署性 | NFR-008 | 一鍵啟動測試 |

## 使用者故事 → 需求對應

| 使用者故事 | 對應需求 | 驗收狀態 |
| --- | --- | --- |
| US-001（依地區瀏覽） | FR-005 | 已滿足 |
| US-007（結構化 JSON） | FR-010, schema | 已滿足 |
| US-008（可驗證來源） | FR-002, NFR-001 | 已滿足 |
| US-014（失敗跳過） | FR-004, NFR-002 | 已滿足 |
| US-015（Issue 同步） | FR-011 | 已滿足 |
| US-016（品質掃描） | NFR-005 | 規劃中 |
| US-017（分支治理） | FR-007, CRM | 已滿足 |

## 狀態定義

| 狀態 | 定義 |
| --- | --- |
| 已實作／已滿足 | 元件已存在並通過驗證 |
| 規劃中 | 已設計但尚未於 CI/CD 完整驗證 |
| 待追蹤 | 需求已記錄但實作尚未開始 |

## 維護規範

本矩陣隨專案演進持續更新。任何需求變更、新增實作元件或驗證方式變更，均須同步更新本矩陣，並依 [變更管理](crm.md) 流程提交。狀態變更應反映於 CHANGELOG。本矩陣為品質保證的關鍵工件，須與 SRS、PRD、PDR 保持一致。
