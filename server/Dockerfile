FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    SERVER_RUNTIME_DIR=/app/runtime \
    TRADINGAGENTS_RESULTS_DIR=/app/runtime/logs \
    TRADINGAGENTS_CACHE_DIR=/app/runtime/cache \
    TRADINGAGENTS_MEMORY_LOG_PATH=/app/runtime/memory/trading_memory.md

WORKDIR /app

COPY pyproject.toml README.md ./
COPY tradingagents ./tradingagents
COPY cli ./cli
COPY server/requirements.txt ./server/requirements.txt

RUN pip install --no-cache-dir -e . -r server/requirements.txt

COPY server ./server

RUN useradd --create-home appuser \
    && mkdir -p /app/runtime \
    && chown -R appuser:appuser /app/runtime

USER appuser

EXPOSE 8000

CMD ["uvicorn", "server.app.main:app", "--host", "0.0.0.0", "--port", "8000"]

