#!/usr/bin/env bash
set -euo pipefail

# Codex workspaces may not have write access to the user's global cache. Keep the
# canonical gate portable while allowing callers to supply their own cache path.
export UV_CACHE_DIR="${UV_CACHE_DIR:-${TMPDIR:-/tmp}/chronos-uv-cache}"
# The production adapter intentionally composes the containing repository's public engine reads.
export PYTHONPATH="src:../../engine/src${PYTHONPATH:+:${PYTHONPATH}}"

uv run ruff format --check .
uv run ruff check .
uv run basedpyright
uv run pytest
