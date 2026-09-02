#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODEL="${1:?usage: $0 <installed-ollama-model>}"
PYTHON="${PYTHON:-$ROOT/.venv/bin/python}"
[[ -x "$PYTHON" ]] || PYTHON=python3
PYTHONPATH="$ROOT/src" "$PYTHON" -m nesy_firewall.cli run-ollama --model "$MODEL" --limit 25 --output "$ROOT/runs/ollama-$MODEL"
