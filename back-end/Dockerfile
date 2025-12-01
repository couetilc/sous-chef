# syntax=docker/dockerfile:1.7
FROM python:3.13-slim AS base

RUN apt-get update && apt-get install -y cron

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

CMD ["/app/entrypoint.sh"]
