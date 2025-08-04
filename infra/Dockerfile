# CrewAI × Agentic Design Patterns 教案專案 Docker 檔案

FROM python:3.11-slim

# 設定工作目錄
WORKDIR /app

# 設定環境變數
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    git \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 複製依賴檔案
COPY requirements.txt pyproject.toml ./

# 安裝 Python 依賴
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# 複製應用程式代碼
COPY src/ ./src/
COPY docs/ ./docs/
COPY infra/ ./infra/

# 複製設定檔案
COPY .env.example .env

# 建立必要的資料夾
RUN mkdir -p storage data uploads logs

# 設定檔案權限
RUN chmod +x infra/scripts/*.sh 2>/dev/null || true

# 健康檢查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 暴露埠號
EXPOSE 8000

# 啟動命令
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"] 