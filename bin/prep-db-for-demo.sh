#!/usr/bin/env bash

# Usage: ./bin/prep-db-for-demo.sh [--prod]
# Default: runs on development stack (compose.yml)
# --prod: runs on production stack (compose.prod.yml)

COMPOSE_FILE="compose.yml"

# Parse arguments
if [ "$1" = "--prod" ]; then
    COMPOSE_FILE="compose.prod.yml"
    echo "Running on production stack (compose.prod.yml)..."
else
    echo "Running on development stack (compose.yml)..."
    echo "Use --prod flag to run on production stack"
fi

docker compose -f "$COMPOSE_FILE" run --rm --remove-orphans backend python manage.py migrate
docker compose -f "$COMPOSE_FILE" run --rm --remove-orphans backend bash -c "\
	python manage.py flush --noinput && \
	python manage.py load_users && \
	python manage.py load_ingredients && \
	python manage.py load_recipes && \
	python manage.py load_diets && \
	python manage.py demo_recipe_history && \
	python manage.py demo_recipes && \
	python manage.py demo_meal_plan && \
	python manage.py load_curated_ingredients --auto-approve && \
	python manage.py load_recipe_curated_ingredients && \
	python manage.py load_recipe_scores && \
	python manage.py load_turkey_scores && \
	echo 'Done!'
	"
