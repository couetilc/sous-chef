#!/usr/bin/env bash
docker compose run --rm backend bash -c "\
	python manage.py flush && \
	python manage.py load_ingredients && \
	python manage.py load_recipes && \
	python manage.py load_diets && \
	python manage.py demo_recipe_history \
	"
