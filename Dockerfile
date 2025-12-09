# syntax=docker/dockerfile:1.5

FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
 # Default value; can be overridden at build time
ARG APP_VERSION=0.0.0
LABEL version="$APP_VERSION"

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        libffi-dev \
        libssl-dev \
    && rm -rf /var/lib/apt/lists/*

FROM base AS deps

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

FROM base AS runtime

ENV PATH="/home/appuser/.local/bin:${PATH}" \
    PYTHONPATH="/app" \
    GOOGLE_APPLICATION_CREDENTIALS="/secrets/sa.json" \
    APP_MODULE="app.main:app" \
    WEB_CONCURRENCY="4" \
    GUNICORN_TIMEOUT="60" \
    HOST="0.0.0.0" \
    PORT="8000" \
    APP_VERSION=$APP_VERSION

RUN useradd --create-home --shell /bin/bash appuser

COPY --from=deps /usr/local/lib/python3.12 /usr/local/lib/python3.12
COPY --from=deps /usr/local/bin /usr/local/bin

COPY app ./app
COPY docs ./docs
COPY kubernetes ./kubernetes
COPY requirements.txt .

RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

CMD ["sh", "-c", "gunicorn ${APP_MODULE} -k uvicorn.workers.UvicornWorker --bind ${HOST}:${PORT} --workers ${WEB_CONCURRENCY} --timeout ${GUNICORN_TIMEOUT}"]
