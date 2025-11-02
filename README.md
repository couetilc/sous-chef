# sous-chef
2025 Fall Purdue CS 307 Team 21

## Developer Setup

### Prepare dependencies

1. Install [Docker](https://www.docker.com/get-started/)

### Quick-start

Rebuild our containers and start our application stack in the background
```
# option "-d": start in the background
# option "--build": rebuild our containers if they've changed
docker compose up -d --build
```

Open a web browser to `localhost:3000`

If you don't have your changes reflected, try
```
docker compose build
docker compose up -d
```

### Front-end

The front-end package manager is [`pnpm`](https://pnpm.io/), it's fast and
modern, which makes it  better than `npm`, while using the same package
registry.

The React files will live in `.jsx` files in `sous-chef/front-end/src/`. Our
front-end assets are managed by [Vite](https://vite.dev/), a program that helps
us develop, manage and compile any files for our front-end project.

**Testing:**
```bash
# Run unit tests
docker compose run frontend pnpm test

# Run integration tests (requires backend running)
docker compose up -d backend db
docker compose run frontend pnpm test:integration
```

If you have dependencies missing:

```
docker compose run frontend pnpm install
```

See [front-end/README.md](front-end/README.md) for detailed testing documentation.

### Back-end

The back-end package manager is [`pip`](https://pypi.org/project/pip/), which
uses the `back-end/requirements.txt` file to re-construct this project's python
dependencies and manage them in a "virtual environment" using
[`venv`](https://docs.python.org/3/library/venv.html).

These are common commands when developing our back-end.
```sh
docker compose up -d # starts all our application containers
docker compose run backend python manage.py migrate # if you have pending migrations
docker compose run backend python manage.py makemigrations # if you've updated a model
docker compose run backend python manage.py createsuperuser # if you need a new admin user
```

### Postgres Database

The postgres database can be accessed via docker. Run these commands to access the database tables.

```sh
# run to view container_id
docker ps

# run with corresponding postgres container_id
docker exec -it <container_id> bash

# log into postgres
psql -h localhost -p 5432 -U dbuser -d api

# view tables in terminal
\d
```

#### Loading Data

**Load Ingredients:**
```sh
# Load canonical ingredients from CSV
docker compose run backend python manage.py load_ingredients

# Preview ingredients without loading (dry-run)
docker compose run backend python manage.py load_ingredients --dry-run

# Load from custom CSV path
docker compose run backend python manage.py load_ingredients --csv-path /path/to/file.csv
```

This command loads 2,211 unique ingredients from `foundation_cleaned_ingredients.csv` with normalized names (title case, trimmed whitespace). The script is idempotent and can be run multiple times safely.

**Load Ingredient Data:**

Make sure you are connected to Postgres on Docker before running.
```sh
chmod +x scraping/ingredient_scraping/load_data.py

./scraping/ingredient_scraping/load_data.py
```

#### Demo Data

**Recipe History Demo:**
```sh
# Load recipes first (if not already loaded)
docker compose run backend python manage.py load_recipes

# Create demo user and sample recipe history data
docker compose run backend python manage.py demo_recipe_history
```

This creates a demo user with comprehensive recipe history data:
- **Username:** `recipe_history`
- **Password:** `password123`
- **Data:** 8 cooked recipes with varying consumption states (0%-100%)
- **Meals:** 18 meals spread across the recipes with realistic timestamps

The command is idempotent and can be run multiple times safely.

#### Database GUI
Install VSCode Extension "Database Client"

Login to postgres using username and password
