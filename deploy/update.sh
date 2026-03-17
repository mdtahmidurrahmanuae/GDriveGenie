#!/usr/bin/env bash
# update.sh — Pull latest code and redeploy GDriveGenie
# Run from the repo root: bash deploy/update.sh
set -euo pipefail

APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$APP_DIR"

echo "[1/3] Pulling latest code..."
git pull origin main

echo "[2/3] Rebuilding and restarting containers..."
docker compose -f docker-compose.prod.yml up -d --build

echo "[3/3] Cleaning up old images..."
docker image prune -f

echo ""
echo "Update complete. App is running at http://$(curl -s ifconfig.me 2>/dev/null || echo '<your-server-ip>')"
