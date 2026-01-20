# Tūhura Tech Sessions Backend

Backend API for the Tūhura Tech Sessions application, built with [Litestar](https://litestar.dev/) and PostgreSQL.

## Requirements

- Python 3.13+
- Docker & Docker Compose (for PostgreSQL and Redis)
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

## Setup

1. **Start the database and Redis:**

   ```bash
   docker compose up -d
   ```

   This starts:
   - PostgreSQL on port 5432
   - Redis on port 6379

2. **Install dependencies:**

   ```bash
   uv sync
   ```

3. **Configure environment:**

   ```bash
   cp .env.example .env
   # Edit .env if needed (defaults work with docker-compose)
   ```

4. **Run migrations + seed sample data (optional):**

   ```bash
   # Apply migrations first
   uv run alembic -c alembic.ini upgrade head
   
   # Then seed sessions + session locations
   uv run python scripts/seed.py
   ```

The seed script is safe to run multiple times: it skips sessions that already exist and reuses matching locations.

1. **Run the development server:**

   ```bash
   uv run python main.py
   ```

   The API will be available at <http://localhost:8000>

1. **Run the background worker (in a separate terminal):**

   ```bash
   uv run saq app.worker.queue_settings
   ```

   The worker processes async tasks like sending emails.

## Database migrations (Alembic)

The app will create tables automatically on startup for development, but production changes should be applied with migrations.

- Apply migrations (local): `uv run alembic -c alembic.ini upgrade head`

When running via Docker Compose, migrations are applied automatically on container start (see `entrypoint.sh`).

### Seeding via Docker

If you're using Docker Compose for Postgres/Redis, you can seed using the built image:

- Start services: `docker compose up -d`
- Seed (runs inside the api image): `docker compose run --rm api uv run python scripts/seed.py`

To reset to a clean database:

- `docker compose down -v`
- `docker compose up -d`
- `docker compose run --rm api uv run python scripts/seed.py`

If a migration fails due to existing data (for example, enforcing a NOT NULL constraint), you must backfill or remove the offending rows before retrying.

## Email Configuration

Emails are sent asynchronously via a background worker using Mailgun. By default, `EMAIL_DRY_RUN=true` which logs emails instead of actually sending them (useful for development/testing).

To enable real email sending:

1. Set `EMAIL_DRY_RUN=false` in `.env`
2. Configure `MAILGUN_API_KEY` and `MAILGUN_DOMAIN`

## API Documentation

- Swagger UI: <http://localhost:8000/docs>
- OpenAPI spec: see [docs/openapi.yaml](../docs/openapi.yaml)

## Project Structure

```text
backend/
├── app/
│   ├── main.py           # Litestar application
│   ├── config.py         # Settings from environment
│   ├── db.py             # Database connection
│   ├── worker.py         # SAQ background worker tasks
│   ├── models/           # SQLAlchemy ORM models
│   │   ├── base.py
│   │   ├── session.py
│   │   ├── signup.py
│   │   ├── caregiver.py
│   │   └── child.py
│   ├── schemas/          # Pydantic request/response schemas
│   │   ├── session.py
│   │   ├── signup.py
│   │   └── common.py
│   ├── services/         # Business logic services
│   │   └── email.py      # Email service (Mailgun + Jinja2)
│   ├── templates/        # Jinja2 templates
│   │   └── email/        # Email templates (HTML + TXT)
│   └── routes/           # API route handlers
│       └── public.py     # Public (caregiver) endpoints
├── scripts/
│   └── seed.py           # Database seeding script
├── docker-compose.yml    # Postgres + Redis for local dev
├── main.py               # Entry point
└── pyproject.toml        # Dependencies
```

## Public Endpoints (Caregiver)

| Method | Path                   | Description                              |
| ------ | ---------------------- | ---------------------------------------- |
| GET    | `/api/sessions`        | List sessions grouped by location        |
| GET    | `/api/session/{id}`    | Get session details                      |
| POST   | `/api/session/{id}`    | Create a signup for a session            |

- `q` - Free-text search over name/address/location
- `region` - Filter by region/location
- `age` - Filter by age group
