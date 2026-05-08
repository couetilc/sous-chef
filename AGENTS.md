# Sous Chef Project Guide

This guide provides AI assistants (and developers) with essential information about the Sous Chef project structure, Docker configuration, and common development commands.

> **IMPORTANT:** All services run through **Docker Compose**. Always access the application through **Caddy on port 3000** (not individual service ports).

## Quick Start

```bash
# 1. Start all services
docker compose up -d

# 2. Run migrations and create superuser
docker compose run backend python manage.py migrate
docker compose run backend python manage.py createsuperuser

# 3. Access application at http://localhost:3000
```

## Architecture Overview

Sous Chef is a full-stack web application with AI-powered recipe search and nutritional analysis:

- **Frontend:** React 19 + Vite 7 + React Router 7
- **Backend:** Django 5.2 + Django REST Framework 3.16
- **Database:** PostgreSQL 16
- **Reverse Proxy:** Caddy (single entry point)
- **AI Features:** LangChain + OpenRouter API for recipe search and nutritional advice
- **Package Managers:** pnpm 8.15.9 (frontend), pip (backend)
- **Testing:** Vitest 3 + Testing Library (frontend), pytest 8 (backend)

## Port Reference

| Service        | Port | Purpose                           | Access Method             |
|----------------|------|-----------------------------------|---------------------------|
| **Caddy**      | **3000** | **Reverse proxy (USE THIS)** | **http://localhost:3000** |
| Frontend       | 5173 | Vite dev server (debugging only)  | http://localhost:5173     |
| Backend        | 8000 | Django dev server (debugging only)| http://localhost:8000     |
| Database       | 5432 | PostgreSQL                        | Database client           |
| Cloudflare Tunnel | n/a | Public ingress (no host ports published) | https://souschef.life |
| Caddy (prod)   | 80   | Internal only (cloudflared → caddy)| (via tunnel)              |

**Note:** In development, always access through Caddy on port 3000. Direct service ports (5173, 8000) are only for debugging specific issues.

## Docker Services

### Development (compose.yml)

1. **db** - PostgreSQL 16
   - Database: `api`, User: `dbuser`, Password: `dbpass`
   - Health check ensures ready before backend starts
   - Persistent volume: `pgdata`

2. **backend** - Django with hot-reload
   - Mounts: `./back-end` → `/app`, `./scraping` → `/scraping`
   - Debug mode enabled
   - Depends on healthy database

3. **frontend** - React + Vite with hot-reload
   - Mounts: `./front-end` → `/app`
   - Anonymous volume for `node_modules` (faster installs)
   - Dev server runs with `--host 0.0.0.0`

4. **caddy** - Reverse proxy (PRIMARY ACCESS)
   - Routes `/admin/*`, `/api/*`, `/static/*`, `/media/*` → backend
   - Routes all other requests → frontend
   - Config: `caddy/Caddyfile.dev`

### Production (compose.prod.yml)

- **db**: PostgreSQL 16. No host ports; uses `pgdata` volume (shared name with dev — same data on this machine).
- **frontend-build**: One-shot. Runs `pnpm install && pnpm build`, writes the static bundle into the `frontend-dist` named volume. Caddy waits for it via `service_completed_successfully`.
- **backend**: Built from `Dockerfile.prod`, runs Gunicorn on internal port 8000.
- **caddy**: Serves the bundle from `frontend-dist` plus `django-static`/`django-media`. Internal port 80 only — TLS terminates at Cloudflare's edge, not here.
- **cloudflared**: Cloudflare Tunnel connector. Reads `cloudflared/config.yml` and the credentials JSON, registers against the tunnel UUID. **The only service exposed to the public internet — and only outbound, via QUIC.**
- **Network**: Custom bridge `sous-chef`.

## Development Workflow

### Common Commands

```bash
# Start/stop services
docker compose up              # Start all (foreground)
docker compose up -d           # Start all (background)
docker compose up backend db   # Start specific services
docker compose down            # Stop all
docker compose down -v         # Stop and delete volumes (WARNING: deletes data)

# View logs
docker compose logs -f         # All services
docker compose logs -f backend # Specific service

# Service status
docker compose ps              # Running containers
docker ps                      # All Docker containers

# Access shells
docker compose exec backend bash   # Backend shell
docker compose exec frontend sh    # Frontend shell
docker compose exec db bash        # Database shell
```

### Database Operations

```bash
# Migrations
docker compose run backend python manage.py migrate
docker compose run backend python manage.py makemigrations

# Superuser
docker compose run backend python manage.py createsuperuser

# Django shell and DB shell
docker compose run backend python manage.py shell
docker compose run backend python manage.py dbshell

# PostgreSQL direct access
docker compose exec db psql -U dbuser -d api
```

### Testing

```bash
# Frontend tests
docker compose run frontend pnpm test                 # Unit tests (watch mode)
docker compose run frontend pnpm test:integration     # Integration tests

# Backend tests
docker compose run backend pytest                     # All tests
docker compose run backend pytest --cov               # With coverage
docker compose run backend pytest -n auto             # Parallel execution
docker compose run backend pytest api/tests/test_foo.py  # Specific file
```

### Installing Dependencies

```bash
# Frontend (pnpm required)
docker compose run frontend pnpm install <package>

# Backend (add to requirements.txt, then)
docker compose down
docker compose build backend
docker compose up -d
```

## Frontend Details

### Key Files
- **Entry Point:** `front-end/src/main.jsx`
- **Pages:** `home.jsx`, `login.jsx`, `createAccount.jsx`, `recipesPage.jsx`, `recipeHistory.jsx`, `inventory.jsx`, `nutritionPage.jsx`, `settingsPage.jsx`
- **API Integration:** `useApi.jsx` (custom hook for all backend calls)
- **User State:** `useUser.jsx`
- **Config:** `vite.config.js`
- **Tests:** `*.test.jsx` files

### Development Notes
- Hot Module Replacement (HMR) works automatically
- Environment variables must be prefixed with `VITE_`
- Tests run in watch mode by default
- Package manager is enforced to pnpm via preinstall script

## Backend Details

### Key Files
- **Models:** `back-end/api/models.py`
- **Views:** `back-end/api/views.py`
- **Serializers:** `back-end/api/serializers.py`
- **URL Routes:** `back-end/api/urls.py`
- **Settings:** `back-end/config/settings.py`
- **Management Commands:** `back-end/api/management/commands/`
- **Tests:** `back-end/api/tests/`

### Admin Interface
Access Django admin at http://localhost:3000/admin/ (requires superuser account)

### API Documentation
Interactive Swagger UI at http://localhost:3000/api/schema/swagger-ui/

### Development Notes
- Always run migrations after pulling code
- Backend expects environment variables from `.env` file
- Use `--dry-run` flags on management commands to preview changes
- Django serves static/media files in development (Caddy proxies them)

## Management Commands

All commands run via: `docker compose run backend python manage.py <command>`

### Data Loading

```bash
# Ingredients
load_ingredients                   # Load canonical ingredients (7,792 items)
  --dry-run                        # Preview without changes
  --csv-path /path/to/file.csv     # Custom CSV path

load_curated_ingredients           # Load curated ingredients (971 staples)
  --auto-approve                   # Skip confirmation
  --clear                          # Clear existing before loading

load_scraped_ingredients           # Load scraped ingredients from CSV
  --dry-run                        # Preview without changes

export_curated_ingredients         # Export curated ingredients to CSV

cluster_ingredients                # Generate curated ingredients using LLM
  --auto-approve                   # Requires OPEN_ROUTER_API_KEY

# Recipes
load_recipes                       # Load recipes from CSV
load_scraped_recipes               # Load scraped recipes
demo_recipes                       # Load 3 demo recipes with ingredient bindings
load_recipeingredients             # Load recipe-ingredient relationships

# Other Data
load_diets                         # Load predefined diets (Vegetarian, Vegan, etc.)
load_inventory                     # Load scraped inventory/pricing data
  --dry-run                        # Preview without changes
  --batch-size 1000                # Bulk insert batch size

load_scraped_nutritional_info      # Load nutritional data from scraping

# Demo Data
demo_recipe_history                # Create demo user with recipe history
                                   # User: recipe_history / password123
                                   # 8 recipes, 18 meals, realistic timestamps

load_users                         # Load demo users
```

## Database Management

### Database Credentials (Development)
- **Host:** `localhost` (or `db` from within Docker)
- **Port:** `5432`
- **Database:** `api`
- **Username:** `dbuser`
- **Password:** `dbpass`

### PostgreSQL Access

```bash
# Via Docker
docker compose exec db psql -U dbuser -d api

# Common psql commands
\d                  # List all tables
\d api_tablename    # Describe table
\q                  # Exit
```

## Environment Variables

Copy `.env.example` to `.env` and customize:

```bash
cp .env.example .env
```

**Key Variables:**
```bash
# Database
POSTGRES_DB=api
POSTGRES_USER=dbuser
POSTGRES_PASSWORD=dbpass

# Django
DJANGO_DEBUG=True
DJANGO_SECRET_KEY=your-secret-key
DJANGO_DB_HOST=db               # Use 'db' for Docker networking
DJANGO_DB_PORT=5432

# API Keys
OPEN_ROUTER_API_KEY=your-key    # Required for AI features
```

**IMPORTANT:** Never commit `.env` to git. It contains secrets and local configuration.

## AI Features

Sous Chef includes AI-powered features using LangChain and OpenRouter:

- **AI Nutritionist:** Chat interface for nutrition advice with tool calling
- **Recipe Search:** AI agent can search recipe database
- **Ingredient Clustering:** LLM-powered ingredient curation (`cluster_ingredients` command)

### Requirements
- Set `OPEN_ROUTER_API_KEY` in `.env`
- Backend dependencies: `langchain`, `langchain-core`, `langchain-openai`

### Related Files
- Nutrition chat: `front-end/src/nutritionPage.jsx`
- Backend AI views: Check `back-end/api/views.py` for AI endpoints

## Directory Structure

```
sous-chef/
├── front-end/              # React application
│   ├── src/                # Components and source files
│   ├── public/             # Static assets
│   ├── Dockerfile          # Dev image
│   └── package.json        # Dependencies and scripts
├── back-end/               # Django application
│   ├── api/                # Main Django app
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── serializers.py
│   │   ├── urls.py
│   │   ├── management/commands/  # Custom commands
│   │   ├── migrations/
│   │   └── tests/
│   ├── config/             # Django configuration
│   ├── Dockerfile          # Dev image
│   ├── Dockerfile.prod     # Prod image
│   ├── manage.py
│   └── requirements.txt
├── scraping/               # Data scraping scripts
│   ├── ingredient_scraping/
│   ├── price_scraping/
│   └── recipe_scraping/
├── caddy/                  # Reverse proxy config
│   ├── Caddyfile           # Production
│   └── Caddyfile.dev       # Development
├── ansible/                # Deployment automation
├── bin/                    # Utility scripts
├── docs/                   # Documentation
├── compose.yml             # Development compose
├── compose.prod.yml        # Production compose
├── .env                    # Environment (git-ignored)
└── .env.example            # Template
```

## Production Deployment

The prod stack defined in `compose.prod.yml` runs in **two places that share the same Cloudflare Tunnel**:

1. **EC2 host** (`54.226.217.180`) — provisioned and updated via Ansible. The canonical, hands-off prod target.
2. **Local laptop** — running `compose.prod.yml` here also registers against the same Cloudflare tunnel, so this machine can serve real `souschef.life` traffic. Useful for ad-hoc deploys / debugging without a remote round-trip.

Both share the tunnel ID in `cloudflared/config.yml`; Cloudflare load-balances across registered connectors. Whichever machine has `cloudflared` running can receive live traffic.

### Public ingress: Cloudflare Tunnel

There is no Let's Encrypt and no published HTTP/HTTPS ports. The `cloudflared` container connects outbound to Cloudflare's edge (QUIC), and `souschef.life` / `www.souschef.life` route inbound through the tunnel to internal `caddy:80`. TLS terminates at Cloudflare.

**Required files (gitignored — do not commit):**
- `.env` — production secrets
- `cloudflared/<TUNNEL-UUID>.json` — tunnel credentials. Without this on disk, `cloudflared` fails to register and the site goes dark. The UUID matches `tunnel:` and `credentials-file:` in `cloudflared/config.yml`.

### Deploy via Ansible (canonical, EC2)

```bash
./bin/deploy.sh
# equivalent to:
ansible-playbook -i ansible/inventory.ini ansible/deploy.yml
```

Copies your local `.env` to the EC2 host, `git pull`s on the remote, and runs `docker compose -f compose.prod.yml up -d --build` there. Prerequisites (SSH key, 1Password agent, etc.) are in `ANSIBLE.md`.

### Deploy locally (laptop-as-prod)

```bash
git pull --ff-only origin main
docker compose -f compose.prod.yml up -d --build
```

Rolling rebuild semantics:
- Backend image rebuilds; `frontend-build` one-shot re-runs and writes a fresh bundle into `frontend-dist`.
- Only the **backend** container is recreated (~5–15s blip).
- `caddy`, `cloudflared`, and `db` keep running. Caddy serves the new JS as soon as `frontend-build` finishes — no caddy restart needed.

First-time cold start on this machine: `docker compose -f compose.prod.yml up -d` (build happens automatically).

### Verifying a deploy

```bash
docker compose -f compose.prod.yml ps                          # all Up / Healthy
docker compose -f compose.prod.yml logs --tail=20 cloudflared  # 4 tunnel connections registered
curl -sI https://souschef.life | head -5                       # 200 OK; last-modified ≈ build time
curl -sI https://souschef.life/api/schema/                     # backend reachable through tunnel
```

If the site is dark, ranked likely causes:
1. `cloudflared/<UUID>.json` missing or invalid → `docker compose logs cloudflared` shows credentials/auth errors.
2. `frontend-build` exited non-zero → `frontend-dist` is empty/stale and caddy returns 404 for `/`. Check its logs.
3. `backend` crashlooping (migration drift, missing env var). Check its logs.
4. Cloudflare-side: tunnel deleted/disabled in dashboard, DNS CNAME removed.

## Utility Scripts

```bash
./bin/deploy.sh                # Ansible deploy to EC2 prod (uses uv to vendor ansible)
./bin/run-prod.sh              # Start the prod stack on this machine: compose.prod.yml up -d
./bin/prod                     # Wrapper: docker compose -f compose.prod.yml "$@"
./bin/prep-db-for-demo.sh      # Flush DB and run data loaders for demos/dev (--prod flag for prod stack)
./bin/git-weekly-summary.sh    # Generate a weekly git summary
./bin/parallel-score.sh        # Score recipes in parallel (ad-hoc data tooling)
./bin/parallel-score-turkey.sh # Variant of parallel-score for Turkey-themed scoring
```

## Testing

The project uses pytest for backend testing with a pragmatic, focused approach.

**Testing Guide**: See [`docs/TESTING.md`](docs/TESTING.md) for comprehensive testing documentation including:
- Testing philosophy and infrastructure
- Patterns and conventions
- Code examples and best practices
- How to write tests for new features

**Quick Start**:
```bash
# Run all tests
docker compose run backend pytest

# Run specific test file
docker compose run backend pytest api/tests/test_nutritionist_chat.py -v

# Run with coverage
docker compose run backend pytest --cov=api

# Run tests in parallel (faster)
docker compose run backend pytest -n auto
```

**Key Testing Principles**:
- Focus on high-value, high-risk areas (critical business logic, data integrity)
- Test tools/functions directly when possible (unit tests)
- Include integration tests for complete workflows
- Mock at appropriate boundaries (e.g., LLM API calls)
- Use descriptive test names and docstrings

**Test Organization**:
- Test files: `back-end/api/tests/test_*.py`
- One test file per feature area
- Test classes group related scenarios
- Global fixtures in `back-end/conftest.py`

## Troubleshooting

### Frontend Not Updating
```bash
# Restart dev server
docker compose restart frontend

# Clear anonymous volume
docker compose down
docker volume rm $(docker volume ls -q | grep node_modules)
docker compose up -d
```

### Backend Database Connection Errors
```bash
# Check database health
docker compose ps db
docker compose logs db

# Restart database
docker compose restart db

# Verify connection from backend
docker compose exec backend python manage.py dbshell
```

### Caddy Routing Issues
```bash
# Check Caddy logs
docker compose logs caddy

# Verify backend/frontend are running
docker compose ps

# Restart Caddy
docker compose restart caddy

# Test backend directly (should see Django response)
curl http://localhost:8000/api/
```

### Port Conflicts
```bash
# Check what's using a port
lsof -i :3000   # or :5173, :8000, :5432

# Stop all Docker services
docker compose down
```

### "Connection Refused" Errors
```bash
# Verify all services running
docker compose ps

# Check logs for errors
docker compose logs
```

### Migrations Out of Sync
```bash
# If you see migration errors after pulling
docker compose run backend python manage.py migrate

# If migrations conflict, may need to reset
docker compose run backend python manage.py migrate --fake
```

### Volume Issues
```bash
# List volumes
docker volume ls

# Remove specific volume (WARNING: deletes data)
docker volume rm sous-chef_pgdata

# Remove all unused volumes
docker volume prune
```

## Helpful Resources

- **Frontend Testing:** `front-end/README.md`
- **Backend Testing:** `back-end/TESTING.md`
- **Deployment:** `ANSIBLE.md`
- **Project Overview:** `README.md`
- **Django Admin:** http://localhost:3000/admin/
- **API Docs:** http://localhost:3000/api/schema/swagger-ui/
