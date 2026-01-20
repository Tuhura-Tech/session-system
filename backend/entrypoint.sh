#!/bin/sh
set -eu

cd /app
export PYTHONPATH="/app${PYTHONPATH:+:$PYTHONPATH}"

# Run Alembic migrations before starting the service.
# docker-compose already waits for Postgres healthcheck, but we retry to avoid transient startup races.
echo "[entrypoint] Running database migrations..."
i=0
until uv run alembic -c alembic.ini upgrade head; do
  i=$((i+1))
  if [ "$i" -ge 5 ]; then
    echo "[entrypoint] Migrations failed after $i attempts." >&2
    exit 1
  fi
  echo "[entrypoint] Migration attempt $i failed; retrying in 2s..." >&2
  sleep 2
done
echo "[entrypoint] Migrations complete."

exec "$@"
