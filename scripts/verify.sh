#!/usr/bin/env bash
set -euo pipefail

if [[ ! -f pyproject.toml ]]; then
  echo "pyproject.toml does not exist yet. Complete Step 01 first."
  exit 1
fi

uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy src
