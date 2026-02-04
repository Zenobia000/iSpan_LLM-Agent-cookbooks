# 🚀 uv 使用說明指南

> **uv** 是一個極快的 Python 套件管理器，用 Rust 編寫，可替代 pip、pip-tools、pipx、poetry、pyenv、virtualenv 等工具。

## 📋 目錄

- [🔧 安裝 uv](#-安裝-uv)
- [🏗️ 專案初始化](#️-專案初始化)
- [📦 依賴管理](#-依賴管理)
- [🔄 虛擬環境管理](#-虛擬環境管理)
- [🛠️ 開發工作流](#️-開發工作流)
- [⚙️ 配置選項](#️-配置選項)
- [🔍 故障排除](#-故障排除)
- [📚 進階功能](#-進階功能)

---

## 🔧 安裝 uv

### 方法一：官方安裝腳本（推薦）

```bash
# Linux/macOS
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 方法二：使用 pip

```bash
pip install uv
```

### 方法三：使用套件管理器

```bash
# macOS (Homebrew)
brew install uv

# Windows (Scoop)
scoop install uv

# Ubuntu/Debian
sudo apt install uv

# Arch Linux
pacman -S uv
```

### 驗證安裝

```bash
uv --version
# 輸出範例：uv 0.9.29
```

---

## 🏗️ 專案初始化

### 從現有專案開始

如果您已有 `pyproject.toml` 檔案：

```bash
# 克隆專案
git clone https://github.com/your-org/project.git
cd project

# 同步依賴並創建虛擬環境
uv sync

# 啟用虛擬環境
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate.bat  # Windows
```

### 創建新專案

```bash
# 初始化新專案
uv init my-project
cd my-project

# 查看生成的檔案結構
tree
# my-project/
# ├── pyproject.toml
# ├── README.md
# ├── .python-version
# └── src/
#     └── my_project/
#         └── __init__.py
```

---

## 📦 依賴管理

### 安裝套件

```bash
# 安裝生產依賴
uv add requests pandas numpy

# 安裝開發依賴
uv add pytest black flake8 --group dev

# 安裝可選依賴組
uv add mkdocs mkdocs-material --group docs

# 安裝特定版本
uv add "fastapi>=0.100.0,<1.0.0"

# 從 Git 安裝
uv add git+https://github.com/user/repo.git

# 從本地路徑安裝
uv add ./local-package

# 以可編輯模式安裝當前專案
uv add -e .
```

### 移除套件

```bash
# 移除套件
uv remove requests

# 移除開發依賴
uv remove pytest --group dev
```

### 同步依賴

```bash
# 同步所有依賴（類似 poetry install）
uv sync

# 只同步生產依賴
uv sync --no-group dev

# 同步特定依賴組
uv sync --group dev --group docs

# 同步並包含額外依賴組
uv sync --extra dev --extra docs
```

### 鎖定檔案管理

```bash
# 更新鎖定檔案
uv lock

# 查看過時的套件
uv tree --outdated

# 升級套件
uv add requests@latest

# 升級所有套件
uv sync --upgrade
```

---

## 🔄 虛擬環境管理

### 創建和管理虛擬環境

```bash
# 創建虛擬環境（在 .venv/ 目錄）
uv venv

# 創建指定名稱的虛擬環境
uv venv my-env

# 創建指定 Python 版本的環境
uv venv --python 3.11

# 啟用虛擬環境
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate.bat  # Windows

# 停用虛擬環境
deactivate

# 移除虛擬環境
rm -rf .venv
```

### Python 版本管理

```bash
# 列出可用的 Python 版本
uv python list

# 安裝特定 Python 版本
uv python install 3.11

# 設定專案 Python 版本
uv python pin 3.11

# 查看當前使用的 Python
uv python find
```

---

## 🛠️ 開發工作流

### 完整開發設置

```bash
# 1. 克隆專案
git clone <repository-url>
cd <project-name>

# 2. 同步開發環境
uv sync --group dev

# 3. 啟用虛擬環境
source .venv/bin/activate

# 4. 設置 pre-commit hooks
pre-commit install

# 5. 運行測試
uv run pytest

# 6. 格式化程式碼
uv run black .
uv run flake8 .

# 7. 型別檢查
uv run mypy .
```

### 執行腳本和命令

```bash
# 在虛擬環境中執行 Python 腳本
uv run python script.py

# 執行模組
uv run -m pytest

# 執行已安裝的命令列工具
uv run black --check .
uv run flake8 src/

# 執行 Jupyter
uv run jupyter lab

# 啟動 FastAPI 應用
uv run uvicorn main:app --reload
```

### 依賴版本鎖定

```bash
# 生成 requirements.txt（用於部署）
uv export --format requirements-txt --output-file requirements.txt

# 生成開發環境 requirements
uv export --format requirements-txt --group dev --output-file requirements-dev.txt

# 從 requirements.txt 安裝（不推薦，建議使用 uv sync）
uv pip install -r requirements.txt
```

---

## ⚙️ 配置選項

### pyproject.toml 配置

```toml
[tool.uv]
# 開發依賴（舊版本相容性）
dev-dependencies = [
    "pytest>=7.0.0",
    "black>=23.0.0",
    "flake8>=6.0.0",
]

# 安裝器配置
installer = "uv"  # 使用 uv 作為安裝器

# 解析器配置
resolution = "highest"  # 或 "lowest-direct"

# 索引配置
index-url = "https://pypi.org/simple/"
extra-index-url = [
    "https://pypi.org/simple/",
]

# 平台配置
python-platforms = ["linux"]

# 工作區配置
workspace = true  # 啟用工作區功能
```

### 環境變量

```bash
# 設定 Python 路徑
export UV_PYTHON=/usr/bin/python3.11

# 設定快取目錄
export UV_CACHE_DIR=/path/to/cache

# 設定設定檔目錄
export UV_CONFIG_FILE=/path/to/uv.toml

# 禁用進度條
export UV_NO_PROGRESS=1

# 設定並行度
export UV_CONCURRENT_DOWNLOADS=10
```

---

## 🔍 故障排除

### 常見問題與解決方案

#### 1. 權限錯誤

```bash
# 問題：Permission denied
# 解決方案：確認檔案權限
sudo chown -R $USER:$USER ~/.local/share/uv/
```

#### 2. Python 版本衝突

```bash
# 問題：Python version conflict
# 解決方案：明確指定 Python 版本
uv venv --python 3.11
uv sync --python-version 3.11
```

#### 3. 依賴解析失敗

```bash
# 問題：依賴衝突
# 解決方案：查看詳細錯誤訊息
uv sync --verbose

# 或使用解析策略
uv sync --resolution lowest-direct
```

#### 4. 網路連線問題

```bash
# 使用鏡像源
uv sync --index-url https://mirrors.aliyun.com/pypi/simple/

# 或設定代理
export HTTP_PROXY=http://proxy.example.com:8080
export HTTPS_PROXY=http://proxy.example.com:8080
```

#### 5. 虛擬環境問題

```bash
# 重新創建虛擬環境
rm -rf .venv
uv venv
uv sync
```

### 除錯命令

```bash
# 查看詳細訊息
uv --verbose sync

# 檢查專案狀態
uv check

# 查看解析樹
uv tree

# 顯示配置資訊
uv config

# 清理快取
uv cache clean
```

---

## 📚 進階功能

### 工作區（Workspace）管理

```toml
# 根目錄 pyproject.toml
[tool.uv.workspace]
members = [
    "packages/*",
    "examples/*"
]

[tool.uv.workspace.dependencies]
shared-utils = { path = "packages/shared-utils" }
```

```bash
# 同步整個工作區
uv sync --workspace

# 只構建特定套件
uv build --package my-package
```

### 腳本執行器

```toml
# pyproject.toml
[tool.uv.scripts]
test = "pytest tests/"
lint = "black --check . && flake8 ."
docs = "mkdocs serve"
dev = "uvicorn main:app --reload"
```

```bash
# 執行定義的腳本
uv run test
uv run lint
uv run docs
uv run dev
```

### 平台特定依賴

```toml
[tool.uv.dependency-groups]
test = [
    "pytest",
    { include-group = "type-check" },
]

type-check = [
    "mypy",
    "types-requests; platform_system == 'Windows'",
]
```

### 自訂索引和認證

```bash
# 使用私有索引
uv add my-private-package --index-url https://private.pypi.org/simple/

# 使用認證
uv add my-package --extra-index-url https://user:pass@private.pypi.org/simple/
```

### 效能最佳化

```bash
# 啟用平行安裝
export UV_CONCURRENT_DOWNLOADS=20

# 使用本地快取
uv sync --cache-dir /path/to/fast/cache

# 預編譯 wheel
uv sync --compile-bytecode
```

---

## 🚀 最佳實務

### 1. 專案結構建議

```
project/
├── pyproject.toml          # 專案配置
├── uv.lock                 # 鎖定檔案
├── .python-version         # Python 版本
├── README.md               # 專案說明
├── src/                    # 原始程式碼
│   └── package_name/
├── tests/                  # 測試檔案
├── docs/                   # 文件
└── .venv/                  # 虛擬環境（git ignore）
```

### 2. CI/CD 整合

```yaml
# .github/workflows/test.yml
name: Test
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install uv
        uses: astral-sh/setup-uv@v1
      - name: Set up Python
        run: uv python install
      - name: Install dependencies
        run: uv sync --group test
      - name: Run tests
        run: uv run pytest
```

### 3. Docker 整合

```dockerfile
FROM python:3.11-slim

# 安裝 uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# 設定工作目錄
WORKDIR /app

# 複製專案檔案
COPY pyproject.toml uv.lock ./

# 安裝依賴
RUN uv sync --no-dev --no-editable

# 複製應用程式碼
COPY . .

# 執行應用
CMD ["uv", "run", "python", "-m", "myapp"]
```

### 4. 版本控制

```gitignore
# .gitignore
.venv/
__pycache__/
*.pyc
.pytest_cache/
.coverage
dist/
build/
*.egg-info/

# 保留這些檔案
# pyproject.toml ✓
# uv.lock ✓
# .python-version ✓
```

---

## 🔗 相關資源

- [uv 官方文件](https://docs.astral.sh/uv/)
- [PyPA 規範](https://packaging.python.org/)
- [PEP 621 - 專案元資料](https://peps.python.org/pep-0621/)
- [uv GitHub](https://github.com/astral-sh/uv)

---

**💡 提示：** uv 持續快速發展中，建議定期更新到最新版本以獲得最佳效能和功能。

```bash
# 更新 uv 到最新版本
uv self update
```