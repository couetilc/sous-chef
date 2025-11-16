#!/usr/bin/env bash
docker compose run --rm --remove-orphans backend bash -c "\
	python manage.py flush --noinput && \
	python manage.py load_users && \
	python manage.py load_recipes && \
	python manage.py load_diets && \
	python manage.py demo_recipe_history && \
	python manage.py demo_recipes && \
	python manage.py demo_meal_plan && \
	echo 'Done!'
	"
