#!/usr/bin/env bash
# start.sh — Render startup script
# 1. Seeds the database (safe to re-run)
# 2. Starts the app under Gunicorn

set -e

echo "=== ADA-1 startup ==="
echo "Running database seed..."
python seed.py

echo "Starting Gunicorn..."
exec gunicorn "run:app" \
  --workers 2 \
  --bind "0.0.0.0:${PORT:-10000}" \
  --timeout 120 \
  --log-level info
