# Contributing to Tūhura Tech Session System

Thanks for your interest in contributing! This repository is a monorepo containing:

- `frontend/` — Public-facing site built with Astro
- `admin_portal/` — Admin UI built with Vite + React
- `backend/` — Litestar API + PostgreSQL

Please take a moment to read this guide so we can review and merge your changes smoothly.

## Code of Conduct & Security

- Be respectful and collaborative. We welcome contributors of all backgrounds.
- Report security vulnerabilities privately via our Security Policy: see `SECURITY.md`.

## Getting Started

1. Fork the repository and clone your fork.
2. Create a branch off `main` using a descriptive name:
   - `feat/<short-topic>` for new features
   - `fix/<short-topic>` for bug fixes
   - `docs/<short-topic>` for docs-only changes
   - `chore/<short-topic>` for tooling/maintenance
3. Open an issue for larger changes first so we can align on scope.

We follow Conventional Commits where possible (e.g., `feat: add children gender`).

## Prerequisites

- Node.js (LTS) and `pnpm`
- Python 3.13+ and [`uv`](https://docs.astral.sh/uv/)
- Docker + Docker Compose (optional for Postgres/Redis)

## Project Setup

### Frontend

```bash
cd frontend
pnpm install
pnpm run dev        # local dev
pnpm run lint:ci    # lint
pnpm run build      # production build
pnpm run test:e2e   # Playwright e2e tests (optional)
```

### Admin Portal

```bash
cd admin_portal
pnpm install
pnpm run dev        # local dev
pnpm run lint:ci    # lint
pnpm run build      # production build
pnpm run test       # Playwright tests
```

### Backend

```bash
cd backend
uv sync                             # install deps
cp .env.example .env                # configure env

# start database services (optional)
docker compose up -d

# apply migrations
uv run alembic -c alembic.ini upgrade head

# run the API
uv run python main.py              # http://localhost:8000

# lint & format
uv run ruff check .
uv run ruff format .

# run tests
uv run pytest -q
```

## Style & Quality

- Keep changes focused; avoid large refactors mixed with features.
- Match existing code style and patterns in each subproject.
- Run linters and tests before submitting a PR.
- For database changes, provide a deterministic Alembic migration and note any backfill steps.

## Pull Requests

- Fill out the PR template and link related issues.
- Include testing instructions (commands and steps) and screenshots where helpful.
- Mark as `Draft` if the work is in progress.
- The CI must be green before review/merge.

## Documentation

- Update `README.md` files and relevant comments when behavior changes.
- If you add environment variables or scripts, document them.

## Licensing

By contributing, you agree that your contributions are licensed under the repository's license (see `LICENSE`).

---

Thank you for helping improve Tūhura Tech Sessions! 🚀
