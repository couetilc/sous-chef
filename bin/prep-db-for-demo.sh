#!/usr/bin/env bash
docker compose run --rm backend bash -c "\
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
	echo 'Done!'
	"
