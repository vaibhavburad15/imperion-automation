#!/bin/bash
# One-shot launcher for the Imperion Automation Platform.
# Builds & starts all services, then seeds the demo data.

set -e

cd "$(dirname "$0")"

echo "🐳 Building and starting containers…"
docker compose up -d --build

echo "⏳ Waiting for backend to be ready…"
for i in {1..30}; do
  if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Backend is up."
    break
  fi
  sleep 2
done

echo "🌱 Seeding demo data…"
docker compose exec -T backend python -m app.seed || true

echo ""
echo "=========================================="
echo "✅ Imperion Automation Platform is ready!"
echo "=========================================="
echo "  Frontend:  http://localhost:5173"
echo "  Backend:   http://localhost:8000"
echo "  API Docs:  http://localhost:8000/docs"
echo ""
echo "  Demo login:"
echo "    admin@acme.com   / password123"
echo "    admin@globex.com / password123"
echo "=========================================="
