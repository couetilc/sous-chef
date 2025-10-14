# sous-chef
2025 Fall Purdue CS 307 Team 21

## Developer Setup

### Prepare dependencies

You should only have to do this once.

1. Install [`direnv`](https://direnv.net/)
```sh
# Once installed, in directory sous-chef/ now run
direnv allow . # activates the .envrc file
```
2. Install [`nodenv`](https://github.com/nodenv/nodenv)
```sh
# Once installed, in directory sous-chef/ now run
nodenv install # installs this project's node version
corepack enable # adds "pnpm" to your PATH
```
3. Install [`pyenv`](https://github.com/pyenv/pyenv)
```sh
# Once installed, in directory sous-chef/ now run
pyenv install # install's this project's python version
```

4. Install [Docker](https://www.docker.com/get-started/)

### Front-end

The front-end package manager is [`pnpm`](https://pnpm.io/), it's fast and
modern, which makes it  better than `npm`, while using the same package
registry.

Run these commands to get started developing:
```
pnpm install
pnpm dev
# opens a browser tab that connects to your front-end dev server
open http://localhost:5173
```

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

See [front-end/README.md](front-end/README.md) for detailed testing documentation.

### Back-end

The back-end package manager is [`pip`](https://pypi.org/project/pip/), which
uses the `back-end/requirements.txt` file to re-construct this project's python
dependencies and manage them in a "virtual environment" using
[`venv`](https://docs.python.org/3/library/venv.html).

Run these commands to get started developing:
```sh
# in the sous-chef/back-end/ directory:
docker compose -f $root/compose.yml up -d # starts the PostgreSQL container
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
# opens a browser tab that connects to your back-end dev server
open http://localhost:8000
```

Our back-end application's main files will live in `sous-chef/back-end/app/`,
while the configuration for our Django server will primarily be in
`sous-chef/back-end/config/`. Remember to activate/deactivate your virtual
environment when you start/stop working, and to start/stop the PostgreSQL
container as well.


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

#### Database GUI
Install VSCode Extension "Database Client"

Login to postgres using username and password