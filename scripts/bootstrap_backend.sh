#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../apps/api"
alembic upgrade head
cd ../..
python3 scripts/seed_master_admin.py

