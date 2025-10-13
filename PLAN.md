# 🎯 目標一覽（更好理解 & 易於實作）

* **M0/M1 用 Mock 工具先跑起來**：不需要任何 API Key，就能把 LangGraph 流程與決策跑通。
* **自動輸出流程圖**：讓節點/邊/分支一眼就懂。
* **極簡回歸集（5 筆黃金路徑）**：先把成功率打滿，再擴充到 20–50 筆。
* **清晰的「升級點」**：從 Mock → MCP provider（Weather/Calendar）替換不痛苦。

---

# 📁 資料夾結構（優化版）

```text
weather-aware-scheduler/
├─ apps/
│  ├─ cli/
│  │  └─ main.py                      # CLI 入口：一句話 → Graph 輸出
│  └─ desktop/
│     └─ prompts.md                   # 可貼到 Claude Desktop 的指令範例
├─ graph/
│  ├─ __init__.py
│  ├─ state.py                        # 狀態/槽位/錯誤/中介資料（pydantic v2）
│  ├─ nodes/
│  │  ├─ intent_and_slots.py          # 意圖&槽位擷取（結構化輸出）
│  │  ├─ check_weather.py             # (M0) MockWeatherTool → (M2+) MCP
│  │  ├─ find_free_slot.py            # (M0) MockCalendarTool → (M2+) MCP
│  │  ├─ confirm_or_adjust.py         # 天氣感知、衝突處理、平移策略
│  │  └─ error_recovery.py            # 重試/追問缺槽/降級
│  └─ build_graph.py                  # 組裝狀態機 & 導出流程圖
├─ chains/
│  ├─ parsers.py                      # 嚴格輸出解析（JSON schema / pydantic）
│  └─ prompts.py                      # Few-shot + 安全/格式約束
├─ tools/
│  ├─ mock_tools.py                   # MockWeatherTool / MockCalendarTool
│  ├─ mcp_adapters.py                 # (M2+) MCP provider → LangChain Tool
│  └─ validators.py                   # 時間/地點正規化&驗證（如時區）
├─ configs/
│  ├─ env.example                     # OPENAI_API_KEY / LANGSMITH_*
│  ├─ graph.config.yaml               # 模型、溫度、重試、超時、門檻
│  └─ claude_desktop_config.json.example  # (M2+) 掛 weather/calendar MCP
├─ datasets/
│  ├─ eval_min5.jsonl                 # ★ 極簡 5 筆黃金路徑
│  └─ eval_full.jsonl                 # 之後擴充到 20–50 筆
├─ observability/
│  ├─ langsmith.yaml                  # 專案名、dataset 名稱、run_tags
│  └─ dashboards.md                   # 追蹤指標與門檻
├─ tests/
│  ├─ test_parsers.py
│  ├─ test_graph_paths.py             # 晴/雨/衝突/缺槽/工具失敗
│  └─ test_tools_contract.py          # (M2+) MCP schema/契約測試
├─ scripts/
│  ├─ dev_run.sh                      # 一鍵：載env→跑CLI→輸出流程圖→開trace
│  ├─ export_graph_viz.py             # 生成 mermaid/graphviz 圖檔
│  ├─ seed_dataset.py                 # 由樣例自動產生/擴充測資
│  └─ replay_eval.py                  # LangSmith 重放&報告
├─ README.md
└─ pyproject.toml / package.json
```

---

# 🛠️ 里程碑與交付（最短 Path to Green）

## M0｜跑得起（Mock 工具，無需 API）

**目標**

* 用 MockWeatherTool/MockCalendarTool 跑通：解析槽位 → 查天氣 → 查空檔 → 建事件 → 回顯。

**交付**

* `tools/mock_tools.py`

  * `MockWeatherTool.get_forecast(city, dt)`

    * 規則：若字串含「雨」或 `dt.hour` 在特定區間則回「高降雨機率」；否則晴天。
  * `MockCalendarTool.find_free_slot(dt, duration)`

    * 規則：週五 15:00 視為「衝突」，其他時間「有空」。
  * `MockCalendarTool.create_event(...)`：回傳事件 id 與回顯摘要。
* `graph/build_graph.py`

  * 將節點串成狀態機；邊包含：**晴→直接建立**、**雨→走調整**、**衝突→找下一空檔再建立**。
  * 內建 `export_graph_viz()`，輸出 `./graph/flow.svg`。
* `scripts/dev_run.sh`

  * `source ./configs/env.example && python apps/cli/main.py "$@" && python scripts/export_graph_viz.py`

**成功檢查**

* 兩條命令跑通：

  * 晴天：`python apps/cli/main.py "週五 14:00 台北與 Alice 會面 60 分鐘"`
  * 雨天：`python apps/cli/main.py "明天下午台北喝咖啡 1 小時（雨備）"`
* 產出 `graph/flow.svg`，README 內嵌顯示。

---

## M1｜智慧決策（可用就有價值）

**目標**

* 天氣高風險 → 自動建議室內或時間平移（±1–2h）；備註加入提醒（帶雨傘、改地點）。
* 衝突 → 自動遞延至下一可用時段（或回傳前三個候選），詢問確認。

**交付**

* `graph/nodes/confirm_or_adjust.py`

  * 策略函式：

    * `if rain_prob > threshold → adjust_time_or_place()`
    * `if conflict → propose_next_free_slot()`
* `chains/parsers.py`：對 `confirm_or_adjust` 的 LLM 輸出做**嚴格 JSON 解析**；失敗即走 `error_recovery`。

**成功檢查**

* 三個 CLI 命令演示：晴天直過、雨天調整、衝突改時段；輸出含「建議原因」與「備註」。

---

## M2｜觀測 & 5 筆極簡回歸（打底品質）

**目標**

* LangSmith 全面 tracing；建立 5 筆黃金路徑回歸集；接上 `scripts/replay_eval.py` 自動出報告。
* 將 Mock 替換為 MCP（可逐一替換：先 weather 後 calendar）。

**交付**

* `datasets/eval_min5.jsonl`（範例）

  1. 晴天 + 有空檔 → 成功建立
  2. 雨天 → 建議室內/平移 + 備註
  3. 衝突 → 下一可用時段
  4. 缺槽（缺日期）→ 單輪追問補齊
  5. 工具失敗（模擬 500）→ 重試 2 次後降級路徑
* `observability/langsmith.yaml`：專案名、dataset、run_tags。
* `tools/mcp_adapters.py`

  * `MCPWeatherTool`、`MCPCalendarTool` 以 adapter 形式暴露**相同介面**，只要在 `graph.config.yaml` 切換開關即可從 Mock→MCP。
* `tests/test_tools_contract.py`：檢查 MCP schema（必填欄位、型別）。

**成功檢查**

* `python scripts/replay_eval.py --dataset datasets/eval_min5.jsonl` 出報告；成功率 ≥ 100%（先用 Mock）。
* 切換到 MCP（至少 weather）後再跑，成功率 ≥ 95%。

---

## M3｜可演示與擴充（面向 Demo）

**目標**

* Claude Desktop 可直接呼叫：附 `configs/claude_desktop_config.json.example` 掛載 MCP providers。
* 輸出更貼近實務：加上地點建議（template），建立事件時帶備註與 URL。

**交付**

* `apps/desktop/prompts.md`：拋光幾條中/英 prompt 範本（含常見變體）。
* `graph/nodes/create_event.py`：將建議寫入備註；返回事件 ID。

**成功檢查**

* 實際用 Claude Desktop 對話完成一次端到端行程建立（看到 MCP 工具被呼叫）。

---

## M4｜加分（選做）

* **RAG**：讀 `knowledge/venues.md`（常用室內/咖啡清單），天氣差時優先建議清單內地點。
* **多模型策略**：解析槽位用便宜模型，決策節點遇到歧義再升級。
* **成本看板**：LangSmith/自製簡表追蹤 token、失敗率、重試次數。

---

# 🧩 關鍵檔案內容（輪廓級）

**`graph/state.py`**

* `SchedulerState`：`city: str | None`, `dt: datetime | None`, `duration_min: int`, `attendees: list[str]`, `weather: {prob_rain:int, desc:str}`, `conflicts: list[TimeRange]`, `proposed: list[TimeRange]`, `error: str | None`.

**`tools/mock_tools.py`**

* `MockWeatherTool.get_forecast(city, dt) -> {prob_rain:int, desc:str}`
* `MockCalendarTool.find_free_slot(dt, duration) -> {status: "ok"|"conflict", next_free: datetime}`
* `MockCalendarTool.create_event(...) -> {event_id:str, summary:str}`

**`graph/build_graph.py`**

* Nodes：`intent_and_slots → check_weather → find_free_slot → confirm_or_adjust → create_event`；
  Edges：按 `rain_prob/conflict` 分支；
  `export_graph_viz()`：輸出 mermaid/graphviz。

**`chains/parsers.py`**

* 定義 pydantic 模型（v2）+ 嚴格 JSON 解析；例外即回 `error_recovery`。

**`graph/nodes/error_recovery.py`**

* 通用重試裝飾器（次數/退避）；缺槽精準追問；最終降級（輸出「人工介入建議」）。

---

# ✅ 成功標準（Definition of Done）

* **M0/M1**：本機無 API Key 跑通三條路徑；輸出 `graph/flow.svg`；CLI 體驗清晰。
* **M2**：LangSmith trace 完整；`eval_min5.jsonl` 100% 全綠；切 MCP（至少天氣）後 ≥ 95%。
* **M3**：Claude Desktop 完成一次真實對話；事件包含備註/連結。
* **文件**：README 有「一鍵啟動、流程圖、三條示例命令、問題排查」。

---

# 🛫 工作順序（每天 1–2 小時也能推進）

1. scaffolding + Mock 工具（M0）
2. 決策節點 & 重試/追問（M1）
3. LangSmith + 5 筆回歸 + 切 MCP（M2）
4. Desktop Demo & 展示文檔（M3）
5. RAG/多模型/看板（M4 選做）