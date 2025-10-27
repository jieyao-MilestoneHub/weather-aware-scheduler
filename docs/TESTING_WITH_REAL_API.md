# 使用真實 OpenAI API 進行測試

## 概述

當設定 `MOCK_MODE=False` 時，系統會使用真實的 OpenAI API 進行天氣預測和行事曆智能調度。

## ⚙️ 環境設定

### 1. 編輯 `.env` 檔案

```bash
# 設定為 False 啟用真實 API
MOCK_MODE=False

# 設定你的 OpenAI API Key
OPENAI_API_KEY=sk-your-actual-openai-key-here

# 或使用 Azure OpenAI（企業用戶）
# AZURE_OPENAI_API_KEY=your-azure-key
# AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
# AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o-mini
# AZURE_OPENAI_API_VERSION=2024-02-15-preview
```

### 2. 獲取 OpenAI API Key

1. 前往 [OpenAI Platform](https://platform.openai.com/api-keys)
2. 登入或註冊帳號
3. 點選 "Create new secret key"
4. 複製 key 並貼到 `.env` 檔案

## 🧪 運行測試

### 使用 Mock 模式（不需要 API Key）

```bash
# 設定 .env
MOCK_MODE=True

# 運行測試
uv run pytest tests/integration/test_sunny_path.py -v
```

**不會呼叫 OpenAI API，使用本地模擬資料**

### 使用真實 API 模式（需要 API Key）

```bash
# 設定 .env
MOCK_MODE=False
OPENAI_API_KEY=sk-your-actual-key

# 運行測試
uv run pytest tests/integration/test_sunny_path.py -v
```

**會實際呼叫 OpenAI API，產生費用！**

## 💰 費用估算

使用 `gpt-4o-mini` 模型（推薦）：

| 測試類型 | 預估 Token | 預估費用 (USD) |
|---------|-----------|---------------|
| 單一測試 (test_sunny_path.py) | ~2,000 tokens | $0.0003 |
| 完整整合測試套件 | ~20,000 tokens | $0.003 |
| 全部測試 (125 tests) | ~100,000 tokens | $0.015 |

**注意**: 實際費用可能因 API 響應長度而異。

## 🔍 驗證 API 使用

### 檢查當前模式

```bash
# 檢查是否會使用 Mock 模式
uv run python -c "
import os
from dotenv import load_dotenv
load_dotenv()
mock_mode = os.getenv('MOCK_MODE', 'true').lower() in ('true', '1', 'yes')
print(f'Mock Mode: {mock_mode}')
print(f'Will call OpenAI API: {not mock_mode}')
"
```

### 測試真實 API 連接

```bash
# 測試天氣工具
uv run python -c "
import os
from dotenv import load_dotenv
load_dotenv()

if os.getenv('MOCK_MODE', 'true').lower() not in ('true', '1', 'yes'):
    from src.tools.real_weather import RealWeatherTool
    from datetime import datetime

    tool = RealWeatherTool()
    result = tool.get_forecast('Taipei', datetime.now())
    print(f'Weather: {result.condition}, {result.temperature}°C')
    print(f'Rain probability: {result.prob_rain}%')
else:
    print('MOCK_MODE is enabled. Set MOCK_MODE=False to test real API.')
"
```

## ⚠️ 重要注意事項

### 1. API Key 安全性

- ❌ **絕對不要** commit `.env` 到 Git
- ✅ `.env` 已在 `.gitignore` 中
- ✅ 使用 `.env.example` 作為模板

### 2. 費用控制

- 運行測試前先檢查 OpenAI 帳戶餘額
- 設定 [Usage Limits](https://platform.openai.com/account/limits) 避免超支
- 大多數測試可在 Mock 模式下運行（免費）

### 3. API 配額限制

OpenAI API 有 Rate Limits：

- **gpt-4o-mini**: 200 requests/min (足夠測試使用)
- **gpt-4**: 10,000 requests/day

如果遇到 `RateLimitError`，請稍後再試或降低並發測試數量。

## 🎯 測試策略建議

### 開發階段

```bash
# 使用 Mock 模式（快速、免費）
MOCK_MODE=True
uv run pytest tests/ -v
```

### CI/CD 階段

```bash
# 使用 Mock 模式（避免 CI 費用）
MOCK_MODE=True
uv run pytest tests/ --cov=src
```

### 上線前驗證

```bash
# 使用真實 API（確保實際行為正確）
MOCK_MODE=False
OPENAI_API_KEY=sk-...
uv run pytest tests/integration/ -v -k "sunny_path or rainy"
```

## 🔧 切換模式的方法

### 方法 1: 修改 .env 檔案（持久）

```bash
# 編輯 .env
MOCK_MODE=False  # 或 True
```

### 方法 2: 環境變數覆蓋（臨時）

```bash
# Windows CMD
set MOCK_MODE=False
uv run pytest tests/integration/test_sunny_path.py -v

# Windows PowerShell
$env:MOCK_MODE="False"
uv run pytest tests/integration/test_sunny_path.py -v

# Linux/Mac
MOCK_MODE=False uv run pytest tests/integration/test_sunny_path.py -v
```

### 方法 3: 程式內檢查

```python
import os
from dotenv import load_dotenv

load_dotenv()
mock_mode = os.getenv("MOCK_MODE", "true").lower() in ("true", "1", "yes")

if mock_mode:
    print("Using Mock Tools (no API calls)")
else:
    print("Using Real Tools (OpenAI API)")
```

## 📊 實際 API 行為 vs Mock 行為

| 功能 | Mock 模式 | 真實 API 模式 |
|------|-----------|---------------|
| **天氣預測** | 固定規則（2-4pm 下雨） | OpenAI 預測（真實天氣模式） |
| **衝突檢測** | 固定時段（Friday 3pm） | OpenAI 智能判斷（考慮常見會議時間） |
| **建議時間** | 簡單遞增（+30min, +60min） | OpenAI 智能建議（考慮工作時間、休息時間） |
| **費用** | 免費 | ~$0.0003/次請求 |
| **速度** | <10ms | 500-2000ms |

## ❓ 常見問題

**Q: 測試失敗，顯示 "OPENAI_API_KEY not set"？**
A: 確認 `.env` 中設定了有效的 API key，且 `MOCK_MODE=False`

**Q: 所有測試都在用 Mock 模式，即使設定了 MOCK_MODE=False？**
A: 檢查 `.env` 是否在專案根目錄，並確認沒有拼寫錯誤（大小寫敏感）

**Q: 測試速度變慢很多？**
A: 這是正常的，真實 API 呼叫需要 500-2000ms，Mock 模式只需 <10ms

**Q: 如何確認真的在呼叫 OpenAI API？**
A: 查看 [OpenAI Usage Dashboard](https://platform.openai.com/usage)，會顯示 API 呼叫次數和費用

**Q: 測試結果和 Mock 模式不同？**
A: 這是正常的！真實 API 使用 AI 預測，結果更智能但也更不確定。Mock 模式是確定性的。

## 🚀 快速驗證腳本

創建 `scripts/test_real_api.sh`:

```bash
#!/bin/bash

# Load .env
source .env

# Check mode
if [ "$MOCK_MODE" = "false" ] || [ "$MOCK_MODE" = "False" ]; then
    echo "Testing with REAL OpenAI API..."
    echo "API Key: ${OPENAI_API_KEY:0:10}..."

    # Run limited tests to avoid high costs
    uv run pytest tests/integration/test_sunny_path.py -v

    echo ""
    echo "Check usage at: https://platform.openai.com/usage"
else
    echo "MOCK_MODE is enabled. Set MOCK_MODE=False in .env to test real API"
fi
```

使用方式：
```bash
chmod +x scripts/test_real_api.sh
./scripts/test_real_api.sh
```

---

**提醒**: 在 CI/CD 和日常開發中建議使用 Mock 模式（快速且免費）。只在需要驗證真實 API 整合時才切換到真實模式。
