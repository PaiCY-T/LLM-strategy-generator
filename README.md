# Finlab Backtesting Optimization System

智能交易策略回測與優化平台，專為週/月交易週期設計。

Intelligent trading strategy backtesting and optimization platform designed for weekly/monthly trading cycles.

---

## 功能特色 Features

- 📊 **自動回測** - 使用 Finlab API 進行完整的策略回測
- 🤖 **AI 驅動優化** - 基於 Claude AI 的策略改進建議
- 📈 **性能指標** - 年化報酬率、夏普比率、最大回撤分析
- 🔄 **迭代學習** - 從每次迭代中學習，提供越來越好的建議
- 💾 **數據緩存** - 本地緩存減少 API 調用，支持離線訪問
- 🌐 **雙語支持** - 繁體中文/英文界面

---

## 系統需求 Requirements

- Python 3.8 或更高版本
- Finlab API 訂閱帳號
- Claude API 金鑰
- 建議 8GB+ RAM（用於大數據集）

---

## 快速開始 Quick Start

### 1. 安裝 Installation

```bash
# Clone repository
git clone <repository-url>
cd finlab

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # For development
```

### 2. 配置 Configuration

#### 步驟 2.1: 獲取 Finlab API Token

1. 訪問 [Finlab 官網](https://www.finlab.tw/)
2. 註冊或登錄您的帳號
3. 進入「API 設定」頁面
4. 生成新的 API Token
5. 複製 Token（格式類似：`finlab_xxxxxxxxxxxxxxxx`）

#### 步驟 2.2: 獲取 Claude API Key

1. 訪問 [Anthropic Console](https://console.anthropic.com/)
2. 創建 Anthropic 帳號（如果沒有）
3. 進入「API Keys」區域
4. 創建新的 API Key
5. 複製 Key（格式類似：`sk-ant-xxxxxxxxxxxxx`）

#### 步驟 2.3: 設置環境變數

```bash
# 複製環境變數範例文件
cp .env.example .env

# 編輯 .env 文件，填入您的實際值
# Linux/Mac:
nano .env

# Windows:
notepad .env
```

**`.env` 文件內容**：
```bash
# 必填：您的 Finlab API Token
FINLAB_API_TOKEN=finlab_your_actual_token_here

# 必填：您的 Claude API Key
CLAUDE_API_KEY=sk-ant-your_actual_key_here

# 選填：日誌級別 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_LEVEL=INFO

# 選填：界面語言 (zh-TW, en-US)
UI_LANGUAGE=zh-TW
```

### 3. 驗證安裝 Verify Installation

```bash
# Run tests to verify setup
pytest tests/ -v

# Check configuration
python -c "from config.settings import Settings; s = Settings(); print('✓ Configuration valid')"
```

如果看到 `✓ Configuration valid`，表示配置成功！

---

## 使用方法 Usage

### 命令行界面 CLI

```bash
# Start Streamlit UI
streamlit run src/ui/app.py

# Run backtest (coming in Phase 3)
python -m src.backtest.run --strategy my_strategy.py

# Data management
python -m src.data.cli download price:收盤價
python -m src.data.cli list-cache
python -m src.data.cli cleanup --days 30
```

### Python API

```python
from src.data import DataManager

# Initialize data manager
dm = DataManager(
    cache_dir="data",
    max_retries=4,
    freshness_days=7
)

# Download data (uses cache if fresh)
data = dm.download_data("price:收盤價")
print(data.head())

# Force refresh
fresh_data = dm.download_data("price:收盤價", force_refresh=True)

# Check cache status
is_fresh, last_updated = dm.check_data_freshness("price:收盤價")
print(f"Data fresh: {is_fresh}, last updated: {last_updated}")

# List available cached datasets
datasets = dm.list_available_datasets()
print(f"Cached datasets: {datasets}")

# Cleanup old cache (>30 days)
removed = dm.cleanup_old_cache(days_threshold=30)
print(f"Removed {removed} old cache files")
```

---

## 項目結構 Project Structure

```
finlab/
├── config/
│   └── settings.py          # Configuration management
├── src/
│   ├── data/                # Data layer (Phase 2 ✓)
│   │   ├── __init__.py      # DataManager
│   │   ├── downloader.py    # Finlab API integration
│   │   ├── cache.py         # Local caching
│   │   └── freshness.py     # Data freshness checking
│   ├── backtest/            # Backtest engine (Phase 4)
│   ├── analysis/            # AI analysis (Phase 7)
│   ├── ui/                  # Streamlit UI (Phase 10)
│   └── utils/               # Utilities (Phase 1 ✓)
│       ├── logger.py        # Logging infrastructure
│       └── exceptions.py    # Custom exceptions
├── data/                    # Data cache directory
├── storage/                 # SQLite database
├── logs/                    # Application logs
├── tests/                   # Test suite
├── qa_reports/              # QA evidence and reports
├── .env.example             # Environment template
├── .env                     # Your configuration (DO NOT COMMIT)
├── requirements.txt         # Production dependencies
├── requirements-dev.txt     # Development dependencies
└── README.md               # This file
```

---

## 開發指南 Development Guide

### 運行測試 Running Tests

```bash
# Run all tests with coverage
pytest tests/ -v --cov=src --cov-report=term-missing

# Run specific test file
pytest tests/test_data.py -v

# Run integration tests (requires valid API tokens)
pytest tests/ -m integration -v

# Run only unit tests (fast)
pytest tests/ -m "not integration" -v
```

### Running Integration Tests

Integration tests validate the system against the real Finlab API and require a valid API token.

**Setup**:
```bash
# Set your Finlab API token
export FINLAB_API_TOKEN=your_finlab_api_token_here

# Or add to .env file
echo "FINLAB_API_TOKEN=your_token" >> .env
```

**Run integration tests only**:
```bash
pytest tests/ -m integration -v
```

**Run all tests except integration**:
```bash
pytest tests/ -m "not integration" -v
```

**Run all tests including integration**:
```bash
pytest tests/ -v
```

**Notes**:
- Integration tests make real API calls (may incur costs/rate limits)
- Tests use lightweight datasets (price:收盤價, fundamental_features:融資餘額, etc.) to minimize API usage
- Tests are automatically skipped if FINLAB_API_TOKEN is not set
- Recommended to run integration tests before production deployment
- Integration tests validate that mocked API behavior matches real Finlab API responses

### 代碼質量檢查 Code Quality

```bash
# Type checking
mypy src/ config/ --strict

# Linting
flake8 src/ config/ tests/ --max-line-length=100

# Auto-formatting
black src/ config/ tests/
```

### QA 流程 QA Workflow

每個任務必須完成以下 QA 步驟：

1. **代碼審查** - `mcp__zen__codereview` (gemini-2.5-flash)
2. **批判性驗證** - `mcp__zen__challenge` (gemini-2.5-pro)
3. **收集證據** - flake8, mypy, pytest 結果
4. **記錄證據** - 保存到 `qa_reports/`

詳見 `.claude/specs/finlab-backtesting-optimization-system/QA_WORKFLOW.md`

---

## 故障排除 Troubleshooting

### 問題: "FINLAB_API_TOKEN environment variable is required"

**解決方案**:
1. 確認已複製 `.env.example` 到 `.env`
2. 確認 `.env` 文件中設置了 `FINLAB_API_TOKEN`
3. 確認 Token 格式正確（應為長字符串）
4. 重啟應用程序以加載新的環境變數

### 問題: "Failed to import finlab package"

**解決方案**:
```bash
pip install finlab
# 或指定版本
pip install "finlab>=0.3.0"
```

### 問題: "Rate limit exceeded" 錯誤

**解決方案**:
- 系統會自動重試（5s, 10s, 20s, 40s 指數退避）
- 如果持續出現，請等待幾分鐘後再試
- 檢查 Finlab API 配額限制

### 問題: 測試失敗

**解決方案**:
```bash
# 清理緩存和日誌
rm -rf data/* logs/* test_data/*

# 重新運行測試
pytest tests/ -v --tb=short
```

---

## 性能優化 Performance Tips

1. **使用緩存** - 默認啟用，避免重複 API 調用
2. **定期清理** - 運行 `cleanup_old_cache()` 移除舊數據
3. **批量下載** - 一次下載多個數據集減少 API 調用
4. **調整新鮮度閾值** - 根據交易頻率調整 `freshness_days`

---

## 安全性 Security

- ⚠️ **絕對不要** 將 `.env` 文件提交到版本控制
- ⚠️ **絕對不要** 在代碼中硬編碼 API Token
- ✅ `.env` 已在 `.gitignore` 中
- ✅ 所有密鑰在日誌中自動遮蔽
- ✅ 路徑穿越攻擊防護已啟用

---

## 貢獻 Contributing

這是個人項目，但歡迎提出建議和問題。

---

## 授權 License

此項目供個人使用。

---

## 聯繫 Contact

如有問題或建議，請在 GitHub 上提交 Issue。

---

## 致謝 Acknowledgments

- [Finlab](https://www.finlab.tw/) - 提供台灣股市數據 API
- [Anthropic Claude](https://www.anthropic.com/) - AI 驅動的策略分析
- [Streamlit](https://streamlit.io/) - 用戶界面框架
