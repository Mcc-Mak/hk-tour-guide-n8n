# 資料結構

本文件定義「香港建築物導賞手冊自動化流水線」中各組件間交換的資料結構，涵蓋建築矩陣結構、`intermediate_research.json` 結構、導賞手冊 Markdown frontmatter 與 runs 目錄結構。所有結構均為 JSON 或 Markdown，並以繁體中文命名關鍵內容欄位。

## 建築矩陣結構

建築矩陣檔案位於 `codebase/建築矩陣.md`，為流水線的輸入來源。檔案合併市區、新界與法定古蹟三大來源，去重後收錄建築物清單。

### Markdown 表格結構

建築矩陣以 Markdown 表格呈現，欄位定義如下：

| 欄位 | 型別 | 說明 |
| --- | --- | --- |
| `編號` | string | 五位數編號（`00001`-`99999`），唯一識別碼 |
| `中文名稱` | string | 建築物中文名稱（保留中文） |
| `中文地址` | string | 建築物中文地址（保留中文） |
| `分類` | string | `法定古蹟`／`新界`／`市區` |
| `興建年份` | string | 可空；建築物興建年份 |
| `備註` | string | 可空；補充資訊 |

### 解析後的內部結構

n8n 讀取建築矩陣後，解析為以下 JSON 陣列供 Loop 迭代：

```json
{
  "buildings": [
    {
      "id": "00001",
      "name": "前九廣鐵路鐘樓",
      "address": "尖沙咀",
      "category": "法定古蹟",
      "year_built": "1915",
      "remark": ""
    }
  ],
  "total": 16005
}
```

### 分類路由對應

| `分類` 值 | 輸出目錄 |
| --- | --- |
| `法定古蹟` | `codebase/導賞手冊/法定古蹟/` |
| `新界` | `codebase/導賞手冊/建築/新界/` |
| `市區` | `codebase/導賞手冊/建築/市區/` |

### 輸出檔名格式

```
{編號}-{中文名稱}-{中文地址}.md
```

範例：`00001-前九廣鐵路鐘樓-尖沙咀.md`

## intermediate_research.json 結構

每座建築物的中介研究狀態寫入 `codebase/.crewai/runs/{building_id}/intermediate_research.json`，作為 CrewAI 與 n8n 間的狀態契約，並供可觀測性與條件判斷使用。

```json
{
  "building_id": "00001",
  "name": "前九廣鐵路鐘樓",
  "category": "法定古蹟",
  "started_at": "2024-10-14T09:00:00Z",
  "updated_at": "2024-10-14T09:02:30Z",
  "attempts": 1,
  "status": "passed",
  "research": {
    "building_info": {
      "year_built": "1915",
      "architect": "建築師姓名",
      "style": "建築風格"
    },
    "historical_context": "歷史背景敘述...",
    "architectural_features": "建築特色敘述...",
    "cultural_significance": "文化意義敘述...",
    "sources": [
      {
        "title": "來源標題",
        "url": "https://example.gov.hk/source",
        "accessed_at": "2024-10-14"
      }
    ]
  },
  "review": {
    "verdict": "passed",
    "confidence_score": 92,
    "issues": []
  },
  "documentation": {
    "output_path": "codebase/導賞手冊/法定古蹟/00001-前九廣鐵路鐘樓-尖沙咀.md",
    "written_at": "2024-10-14T09:02:25Z"
  },
  "steps": [
    {
      "ts": "2024-10-14T09:00:05Z",
      "agent": "archival_researcher",
      "event": "step",
      "payload": "中間思考片段..."
    }
  ]
}
```

### 欄位說明

| 欄位 | 說明 |
| --- | --- |
| `status` | `researching`／`reviewing`／`passed`／`failed`／`skipped` |
| `attempts` | 硬關卡審查嘗試次數（上限 3） |
| `review.verdict` | `passed` 或 `failed` |
| `review.confidence_score` | 0-100 |
| `review.issues` | 不通過問題清單，每項含位置、描述、建議 |
| `steps` | `step_callback`／`task_callback` 捕捉的中間思考與對話 |

### 跳過狀態範例

五次未通過時，`status` 為 `skipped`，並附加 `exception` 區塊：

```json
{
  "status": "skipped",
  "attempts": 5,
  "exception": {
    "log_path": "codebase/.crewai/runs/00001/exception.log",
    "reason": "硬關卡五次未通過",
    "last_issues": [...]
  }
}
```

### 提示詞工作流中介狀態

提示詞工作流的狀態寫入 `codebase/.crewai/runs/prompt-workflow/intermediate_state.json`，結構相似但 `building_id` 改為 `workflow` 欄位，記錄鷹架產出進度。

## 導賞手冊 Markdown frontmatter

每份導賞手冊以 YAML frontmatter 開頭，提供結構化元資料供 mdBook 與程式化取用。

```yaml
---
building_id: "00001"
name: "前九廣鐵路鐘樓"
address: "尖沙咀"
category: "法定古蹟"
year_built: "1915"
architect: "建築師姓名"
style: "建築風格"
confidence_score: 92
review_verdict: "passed"
generated_at: "2024-10-14T09:02:25Z"
sources_count: 5
---
```

### frontmatter 欄位規範

| 欄位 | 必填 | 說明 |
| --- | --- | --- |
| `building_id` | 是 | 五位編號，與矩陣一致 |
| `name` | 是 | 中文名稱（保留中文） |
| `address` | 是 | 中文地址（保留中文） |
| `category` | 是 | 分類，決定目錄 |
| `year_built` | 否 | 興建年份 |
| `architect` | 否 | 建築師 |
| `style` | 否 | 建築風格 |
| `confidence_score` | 是 | 硬關卡信心分數 0-100 |
| `review_verdict` | 是 | 審查結果 |
| `generated_at` | 是 | ISO8601 產出時間 |
| `sources_count` | 是 | 參考來源數量 |

### 手冊主體結構

frontmatter 之後為手冊主體，章節順序為：標題（H1）→ 建築物資訊框 → 歷史沿革 → 建築特色 → 導賞路線 → 參考資料。參考資料區必須列出所有來源（標題、URL、存取日期）。

## runs 目錄結構

`codebase/.crewai/runs/` 目錄保存每次迭代的中間狀態與日誌，供可觀測性與除錯使用。

```
codebase/.crewai/runs/
├── prompt-workflow/
│   ├── intermediate_state.json
│   └── exception.log
├── 00001/
│   ├── intermediate_research.json
│   ├── exception.log
│   └── stdout.log
├── 00002/
│   ├── intermediate_research.json
│   └── stdout.log
└── ...
```

### 檔案用途

| 檔案 | 用途 |
| --- | --- |
| `intermediate_research.json` | 該建築物的完整中介狀態（研究、審查、產出、步驟） |
| `intermediate_state.json` | 提示詞工作流的鷹架產出狀態 |
| `exception.log` | 硬關卡失敗或嚴重錯誤的 Exception Log |
| `stdout.log` | n8n 擷取的 Python 腳本 stdout 日誌 |

### 命名規則

- 建築物目錄以五位編號命名（如 `00001`），與建築矩陣 `編號` 一致。
- 提示詞工作流目錄固定為 `prompt-workflow`。
- 所有 JSON 檔案為 UTF-8 編碼，含 BOM 否均可，但欄位值為繁體中文。

### 保留期限

runs 目錄為可觀測性資料，不納入 mdBook 發佈，但納入 Git 版本控制以供追溯。如空間不足，可依變更管理流程清理較舊的 `stdout.log`，但 `intermediate_research.json` 與 `exception.log` 應保留以維持可追溯性。
