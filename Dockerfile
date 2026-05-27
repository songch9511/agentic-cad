FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl libgl1 libglib2.0-0 libxrender1 libxext6 \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md Dockerfile compose.yaml ./
COPY src ./src
COPY tests ./tests
COPY data ./data
COPY docs ./docs
COPY scripts ./scripts

RUN pip install --upgrade pip \
    && pip install -e '.[cad,api]' pytest

RUN chmod +x scripts/*.sh 2>/dev/null || true \
    && python -m compileall src/cadx tests \
    && cadx run-demo \
    && cadx validate \
    && pytest -q tests/test_server.py

EXPOSE 8000

CMD ["uvicorn", "cadx.server:app", "--host", "0.0.0.0", "--port", "8000"]
