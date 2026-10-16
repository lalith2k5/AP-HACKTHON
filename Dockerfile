# StoreSignal AI — container image
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app/src

RUN apt-get update \
 && apt-get install -y --no-install-recommends curl ca-certificates make \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies (wheel cache reused across builds)
COPY requirements.txt ./
RUN pip install --upgrade pip \
 && pip install -r requirements.txt

# Copy project
COPY config ./config
COPY src ./src
COPY tests ./tests
COPY Makefile ./Makefile
COPY pyproject.toml ./pyproject.toml
COPY README.md ./README.md

# Data directories (populated at runtime by `make pipeline`)
RUN mkdir -p /app/data/raw /app/data/reference /app/data/processed \
             /app/data/processed/briefs /app/data/evaluation/reports /app/models

EXPOSE 8000 8501

CMD ["uvicorn", "api:app", "--app-dir", "/app/src", "--host", "0.0.0.0", "--port", "8000"]
