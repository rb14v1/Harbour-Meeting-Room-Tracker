# syntax=docker/dockerfile:1
FROM python:3.13-slim AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends gcc libc6-dev && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DJANGO_SETTINGS_MODULE=config.settings \
    PORT=8080

RUN groupadd --gid 1000 appuser && useradd --uid 1000 --gid 1000 --create-home appuser

COPY --from=builder /install /usr/local

WORKDIR /app

COPY --chown=appuser:appuser manage.py ./manage.py
COPY --chown=appuser:appuser config ./config
COPY --chown=appuser:appuser meetings ./meetings
COPY --chown=appuser:appuser requirements.txt ./requirements.txt
COPY --chown=appuser:appuser entrypoint.sh ./entrypoint.sh

RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8080/healthz', timeout=4).status==200 else 1)" || exit 1

CMD ["sh", "/app/entrypoint.sh"]
