"""Inject the approved read-only secret into the public Chronos corpus command."""

from __future__ import annotations

import os
from urllib.parse import quote

from research_agent.data_adapters.polymarket.corpus_snapshot import main
from tools.dev.prod_secrets import read_secret


if __name__ == "__main__":
    password = quote(read_secret("human_ro_password"), safe="")
    os.environ["POLYMARKET_DATABASE_URL"] = (
        f"postgresql://human_ro:{password}@127.0.0.1:15432/bdl"
    )
    raise SystemExit(main())
