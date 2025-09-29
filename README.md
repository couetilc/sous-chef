# sous-chef
2025 Fall Purdue CS 307 Team 21

## Architecture Decisions

### Front-end

The front-end package manager is [`pnpm`](https://pnpm.io/), it's fast and
modern, which makes it  better than `npm`, while using the same package
registry.

Run these commands to get started developing:
```
pnpm install
pnpm dev
open http://localhost:5173 # opens a browser tab that connects to your dev server
```

### Back-end

## Developer Setup

1. Install [`direnv`](https://direnv.net/)
```
# In directory sous-chef/ now run
direnv allow . # activates the .envrc file
```
2. Install [`nodenv`](https://github.com/nodenv/nodenv)
```
# In directory sous-chef/ now run
nodenv install # installs this project's node version
corepack enable # adds "pnpm" to your PATH
```
