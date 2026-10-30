"""Fail-closed command tests for the live Polymarket smoke boundary."""

# ruff: noqa: SLF001
# pyright: reportPrivateUsage=false

from __future__ import annotations

import json
import tomllib
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from research_agent.data_adapters.polymarket import smoke

if TYPE_CHECKING:
    from collections.abc import Mapping

BLOCKED_EXIT = 2


def test_standalone_package_declares_live_database_driver() -> None:
    """The documented live smoke must work in Chronos' own environment."""
    project = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    dependencies = project["project"]["dependencies"]

    assert any(item.startswith("asyncpg>=") for item in dependencies)
    assert any(item.startswith("prometheus-client>=") for item in dependencies)
    assert any(item.startswith("tenacity>=") for item in dependencies)


def test_smoke_without_approved_database_url_is_explicitly_blocked(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """No configured read-only connection remains a visible non-live blocker."""
    monkeypatch.delenv("POLYMARKET_DATABASE_URL", raising=False)

    status = smoke.main(["--market-id", "0xmarket"])
    payload = json.loads(capsys.readouterr().out)

    assert status == BLOCKED_EXIT
    assert payload["status"] == "BLOCKED"
    assert payload["error_code"] == "READ_ONLY_DATABASE_URL_UNSET"
    assert payload["live_data_read"] is False
    assert "password" not in json.dumps(payload).casefold()


def _proved_role(**overrides: object) -> Mapping[str, object]:
    role: dict[str, object] = {
        "role": "human_ro",
        "default_read_only": "on",
        "transaction_read_only": "on",
        "can_insert_markets": False,
        "can_update_markets": False,
        "can_insert_fills": False,
        "can_update_fills": False,
        "can_insert_price_series": False,
        "can_update_price_series": False,
        "can_insert_resolutions": False,
        "can_update_resolutions": False,
    }
    role.update(overrides)
    return role


def test_smoke_accepts_only_the_complete_read_only_proof() -> None:
    """Every expected role, setting, and table privilege must be explicit."""
    smoke._require_read_only_role(_proved_role())


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("role", "postgres"),
        ("default_read_only", "off"),
        ("transaction_read_only", "off"),
        ("can_insert_markets", True),
        ("can_update_markets", True),
        ("can_insert_fills", True),
        ("can_update_fills", True),
        ("can_update_fills", None),
        ("can_insert_price_series", True),
        ("can_update_price_series", True),
        ("can_insert_resolutions", True),
        ("can_update_resolutions", True),
    ],
)
def test_smoke_rejects_incomplete_or_writable_role_proof(key: str, value: object) -> None:
    """A true or unknown write privilege can never pass as read-only."""
    with pytest.raises(RuntimeError, match="did not prove"):
        smoke._require_read_only_role(_proved_role(**{key: value}))
