#!/usr/bin/env bash
docker compose up -d \
	-f "../compose.prod.yml" \
	--env-file "../.env"
