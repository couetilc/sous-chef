# Sous Chef Dev Container

A unified development environment that works identically on Windows, macOS, and Linux.

## What This Gives You

- **Full-stack tooling**: Python 3.13, Node.js 24.9, pnpm, PostgreSQL client
- **IntelliSense for everything**: Python type checking, React completion, database queries
- **Consistent environment**: Same Linux setup regardless of your host OS
- **Hot reload**: Backend and frontend services auto-reload on code changes
- **All services connected**: Access db, backend, frontend, nginx from one place

## First-Time Setup

1. **Prerequisites**:
   - Install [Docker Desktop](https://www.docker.com/products/docker-desktop/)
   - Install [VSCode](https://code.visualstudio.com/)
   - Install the [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)

2. **Open in container**:
   ```bash
   # Open the project in VSCode
   code .

   # VSCode will prompt: "Reopen in Container"
   # Click it, or run: Command Palette → "Dev Containers: Reopen in Container"
   ```

3. **Wait for setup** (first time only):
   - Docker builds the dev container (~3-5 minutes)
   - Installs Python dependencies
   - Installs Node dependencies
   - Starts all services (db, backend, frontend, nginx)

## Daily Workflow

### Starting Your Day

Open VSCode → It reopens in the dev container → All services start automatically.

**Access points**:
- **Application**: http://localhost:3000 (via nginx)
- **Frontend**: http://localhost:5173 (Vite dev server)
- **Backend API**: http://localhost:8000 (Django)
- **Database**: localhost:5432

### How Services Work

```
┌─────────────────────────────────────────────┐
│  Your Code (Windows/macOS/Linux)            │
│  /Users/you/repos/sous-chef/                │
└──────────────────┬──────────────────────────┘
                   │ (mounted)
                   ↓
┌─────────────────────────────────────────────┐
│  Dev Container                              │
│  /workspace/                                │
│  ├── Edit code, run commands here           │
│  ├── Full Python + Node tooling             │
│  └── Access: db, backend, frontend          │
└─────────────────────────────────────────────┘
                   │
        ┌──────────┼──────────┬─────────┐
        ↓          ↓          ↓         ↓
     ┌────┐   ┌─────────┐  ┌────────┐  ┌─────┐
     │ db │   │ backend │  │frontend│  │nginx│
     └────┘   └─────────┘  └────────┘  └─────┘
       ↑           ↑           ↑          ↑
    Auto-runs   Auto-runs   Auto-runs  Auto-runs
    Hot reload  Hot reload
```

**Key principle**:
- Backend/frontend services **run automatically** and hot reload
- Dev container is for **editing code** and **running commands**

## Common Tasks

### Backend (Python/Django)

```bash
# All commands run from /workspace in the dev container terminal

# Run migrations
cd back-end
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Open Django shell
python manage.py shell

# Run tests
pytest

# Check types
mypy .
```

### Frontend (React/Vite)

```bash
# Build production bundle
cd front-end
pnpm build

# Run linter
pnpm lint  # (if configured)

# Add new package
pnpm add react-query
```

### Database

```bash
# Connect to PostgreSQL
psql -h db -U dbuser -d api
# Password: dbpass

# From psql prompt:
\dt              # List tables
\d recipes       # Describe table
SELECT * FROM recipes LIMIT 10;
```

### Docker Commands

```bash
# View running services
docker compose ps

# View logs
docker compose logs backend
docker compose logs frontend -f  # Follow logs

# Restart a service
docker compose restart backend

# Run command in backend container
docker compose exec backend python manage.py shell

# Run command in frontend container
docker compose exec frontend pnpm build
```

## Editing Code

**You can edit any file** in the workspace with full IntelliSense:

- **Python files**: Pylance provides type checking, auto-imports, refactoring
- **JavaScript/JSX files**: ESLint, Prettier, React completions
- **Config files**: Syntax highlighting, validation

Changes to code are **immediately synced** to running services thanks to volume mounts.

## Debugging

### Backend Debugging

The backend runs in its own container. To debug:

**Option 1: Print debugging** (easiest)
```python
# Add print statements or logging
print(f"User: {user}")
logger.info(f"Processing {recipe_id}")
```
View output: `docker compose logs backend -f`

**Option 2: Attach debugger**
1. Install `debugpy` in backend container
2. Modify backend startup to use debugpy
3. Use VSCode "Attach to Remote" configuration

### Frontend Debugging

Use browser DevTools:
- Open http://localhost:5173 in Chrome/Firefox
- React DevTools extension recommended
- Console logs appear in browser console

## When to Use What

| Task | Where to Run | Why |
|------|--------------|-----|
| Edit Python/JS files | Dev container | Full IntelliSense |
| Run migrations | Dev container | Has Django + db access |
| Run tests | Dev container | Isolated, repeatable |
| Install packages | Dev container | Updates requirements.txt / package.json |
| View app in browser | Host machine | http://localhost:3000 |
| Debug backend logs | Host machine | `docker compose logs backend` |
| Database queries | Dev container | psql installed |

## Troubleshooting

### "Port already in use"

Stop services on host machine using ports 3000, 5173, 8000, or 5432.

```bash
# Find what's using port 8000
lsof -i :8000

# Stop it or use docker compose down
docker compose down
```

### "Dependencies not found"

Re-run installation:

```bash
# In dev container terminal
cd /workspace/back-end && pip install -r requirements.txt
cd /workspace/front-end && pnpm install
```

### Slow file watching (macOS/Windows)

This is a known Docker Desktop limitation. Workarounds:
- Use `:cached` mount (already configured)
- Limit file watching to specific directories in Vite config
- Consider using VSCode's "Clone in Volume" for better performance

### Need to rebuild

```bash
# From host machine (outside container)
docker compose down
docker compose build devcontainer
docker compose up -d

# Reopen VSCode in container
```

### Services not talking to each other

Services communicate via Docker network using hostnames:
- `db` → PostgreSQL
- `backend` → Django API
- `frontend` → Vite dev server
- `nginx` → Reverse proxy

From dev container:
```bash
# Should work
curl http://backend:8000/api/health
curl http://frontend:5173
psql -h db -U dbuser -d api
```

## Tips

- **Terminal multiplexing**: Open multiple terminals in VSCode (backend commands in one, frontend in another)
- **Git**: Use from inside dev container (same repo, credentials forwarded)
- **Extensions**: Add more in `.devcontainer/devcontainer.json` and rebuild
- **Performance**: Named volumes for `pip-cache` and `pnpm-store` speed up rebuilds

## Architecture Decision

We use **Approach 2: Dedicated Dev Service**:

- ✅ Backend/frontend run separately with hot reload
- ✅ Dev container has both Python and Node
- ✅ Production containers stay clean
- ✅ Full-stack development from one environment

This means you **edit in dev container**, but **services run in their own containers**. This keeps concerns separated and mirrors production architecture.
