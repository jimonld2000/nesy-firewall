#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON="${PYTHON:-$ROOT/.venv/bin/python}"
[[ -x "$PYTHON" ]] || PYTHON=python3
PYTHONPATH="$ROOT/src" "$PYTHON" -m nesy_firewall.cli benchmark --limit 10 --output "$ROOT/runs/smoke"
