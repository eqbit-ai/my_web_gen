#!/bin/sh
# Run pending Alembic migrations then exec the main process.
# Idempotent — alembic upgrade is a no-op if DB is already at head.
set -e

if [ -z "$SKIP_MIGRATIONS" ]; then
  echo "[entrypoint] running alembic upgrade head…"
  alembic upgrade head || {
    echo "[entrypoint] alembic upgrade failed — continuing anyway so the API can serve health checks"
  }
fi

exec "$@"
