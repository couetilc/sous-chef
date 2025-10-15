#!/usr/bin/env bash
docker compose \
	-f "compose.prod.yml" \
	--env-file ".env" \
	up -d
