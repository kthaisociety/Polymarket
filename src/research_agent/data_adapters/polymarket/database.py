"""Fail-closed composition of the approved production read-only database boundary."""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

from research_agent.data_adapters.polymarket.ingestion import ingest_polymarket_contract_tape
from research_agent.data_adapters.polymarket.reader import EnginePolymarketResearchReader

if TYPE_CHECKING:
    from collections.abc import Mapping

    from research_agent.data_adapters.polymarket.ingestion import PolymarketIngestionResult
    from research_agent.data_adapters.polymarket.models import PolymarketImportRequest


async def read_live_polymarket_tape(
    database_url: str,
    request: PolymarketImportRequest,
) -> PolymarketIngestionResult:
    """Prove `human_ro`, read one exact tape, and close the production pool."""
    from core.db.pool import (  # noqa: PLC0415 - optional BDL composition dependency
        close_pool,
        create_pool,
    )

    pool = await create_pool(
        database_url,
        min_size=1,
        max_size=1,
        connect_timeout=timedelta(seconds=10),
        command_timeout=timedelta(minutes=5),
    )
    try:
        async with pool.acquire() as connection:
            role = await connection.fetchrow(_READ_ONLY_PROOF_QUERY)
        require_read_only_role(role)
        return await ingest_polymarket_contract_tape(
            EnginePolymarketResearchReader(pool),
            request,
        )
    finally:
        await close_pool(pool)


def require_read_only_role(role: Mapping[str, object] | None) -> None:
    """Fail unless the connection proves every required read-only condition explicitly."""
    write_privileges = (
        "can_insert_markets",
        "can_update_markets",
        "can_insert_fills",
        "can_update_fills",
    )
    if (
        role is None
        or role.get("role") != "human_ro"
        or role.get("default_read_only") != "on"
        or role.get("transaction_read_only") != "on"
        or any(role.get(privilege) is not False for privilege in write_privileges)
    ):
        msg = "database role did not prove the approved human_ro read-only contract"
        raise RuntimeError(msg)


_READ_ONLY_PROOF_QUERY = (
    "SELECT current_user AS role, "
    "current_setting('default_transaction_read_only') AS default_read_only, "
    "current_setting('transaction_read_only') AS transaction_read_only, "
    "has_table_privilege(current_user, 'market.markets', 'INSERT') "
    "AS can_insert_markets, "
    "has_table_privilege(current_user, 'market.markets', 'UPDATE') "
    "AS can_update_markets, "
    "has_table_privilege(current_user, 'market.fills', 'INSERT') AS can_insert_fills, "
    "has_table_privilege(current_user, 'market.fills', 'UPDATE') AS can_update_fills"
)
