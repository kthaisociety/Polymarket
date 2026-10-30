"""Invoke the public fill snapshot command through the approved local tunnel."""

# ruff: noqa: INP001

from __future__ import annotations

import os
from urllib.parse import quote

from tools.dev.prod_secrets import read_secret

from research_agent.data_adapters.polymarket.behavioral_fill_snapshot import main

if __name__ == "__main__":
    password = quote(read_secret("human_ro_password"), safe="")
    os.environ["POLYMARKET_DATABASE_URL"] = (
        f"postgresql://human_ro:{password}@127.0.0.1:15432/bdl"
    )
    raise SystemExit(main())
