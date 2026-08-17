"""Fail-closed composition of the approved production read-only database boundary."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import TYPE_CHECKING

from research_agent.data_adapters.polymarket.corpus import (
    PolymarketCorpusRegistration,
    PolymarketCorpusRetention,
    PolymarketCorpusStore,
    register_polymarket_resolution_corpus,
)
from research_agent.data_adapters.polymarket.ingestion import ingest_polymarket_contract_tape
from research_agent.data_adapters.polymarket.reader import (
    DatabasePolymarketCorpusReader,
    EnginePolymarketResearchReader,
)

if TYPE_CHECKING:
    from collections.abc import Mapping

    from research_agent.data_adapters.polymarket.ingestion import PolymarketIngestionResult
    from research_agent.data_adapters.polymarket.models import (
        PolymarketCorpus,
        PolymarketCorpusRequest,
        PolymarketImportRequest,
    )


@dataclass(frozen=True, slots=True)
class LivePolymarketCorpusResult:
    """Exact retained and registered result of one production corpus read."""

    corpus: PolymarketCorpus
    retention: PolymarketCorpusRetention
    registration: PolymarketCorpusRegistration


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


async def read_live_polymarket_resolution_corpus(
    database_url: str,
    request: PolymarketCorpusRequest,
    store: PolymarketCorpusStore,
) -> LivePolymarketCorpusResult:
    """Read one repeatable snapshot, retain exact bytes, and register both clocks."""
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
        async with (
            pool.acquire() as connection,
            connection.transaction(isolation="repeatable_read", readonly=True),
        ):
            role = await connection.fetchrow(_READ_ONLY_PROOF_QUERY)
            require_read_only_role(role)
            corpus = await DatabasePolymarketCorpusReader(connection).read_corpus(request)
        retention = store.retain(corpus)
        snapshot = store.load(retention.ref)
        registration = register_polymarket_resolution_corpus(snapshot)
        return LivePolymarketCorpusResult(corpus, retention, registration)
    finally:
        await close_pool(pool)


def require_read_only_role(role: Mapping[str, object] | None) -> None:
    """Fail unless the connection proves every required read-only condition explicitly."""
    write_privileges = (
        "can_insert_markets",
        "can_update_markets",
        "can_insert_fills",
        "can_update_fills",
        "can_insert_price_series",
        "can_update_price_series",
        "can_insert_resolutions",
        "can_update_resolutions",
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
    "has_table_privilege(current_user, 'market.fills', 'UPDATE') AS can_update_fills, "
    "has_table_privilege(current_user, 'market.price_series', 'INSERT') "
    "AS can_insert_price_series, "
    "has_table_privilege(current_user, 'market.price_series', 'UPDATE') "
    "AS can_update_price_series, "
    "has_table_privilege(current_user, 'market.resolutions', 'INSERT') "
    "AS can_insert_resolutions, "
    "has_table_privilege(current_user, 'market.resolutions', 'UPDATE') "
    "AS can_update_resolutions"
)
