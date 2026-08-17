#!/usr/bin/env bash
set -euo pipefail

# Codex workspaces may not have write access to the user's global cache. Keep the
# canonical gate portable while allowing callers to supply their own cache path.
export UV_CACHE_DIR="${UV_CACHE_DIR:-${TMPDIR:-/tmp}/chronos-uv-cache}"
# The production adapter intentionally composes the containing repository's public engine reads.
export PYTHONPATH="src:../../engine/src${PYTHONPATH:+:${PYTHONPATH}}"

if command -v uv >/dev/null 2>&1; then
  uv run ruff format --check .
  uv run ruff check .
  uv run basedpyright
  uv run pytest
elif [[ -x .venv/bin/ruff && -x .venv/bin/basedpyright && -x .venv/bin/pytest ]]; then
  .venv/bin/ruff format --check .
  .venv/bin/ruff check .
  .venv/bin/basedpyright
  .venv/bin/pytest
else
  echo "Chronos checks require uv or a populated .venv" >&2
  exit 127
fi
