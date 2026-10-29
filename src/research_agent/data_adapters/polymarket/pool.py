"""Standalone async PostgreSQL pool for Chronos read-only adapters."""

from __future__ import annotations

import json
from datetime import timedelta
from importlib import import_module
from typing import TYPE_CHECKING, Final, Protocol, cast

from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable, Mapping, Sequence
    from contextlib import AbstractAsyncContextManager


class DatabaseConnection(Protocol):
    """Typed async database surface used by Chronos composition."""

    async def set_type_codec(
        self,
        typename: str,
        *,
        encoder: Callable[[object], str],
        decoder: Callable[[str], object],
        schema: str,
    ) -> None:
        """Register one connection-local value codec."""
        ...

    async def fetch(self, query: str, *args: object) -> Sequence[Mapping[str, object]]:
        """Return rows for one parameterized query."""
        ...

    async def fetchrow(self, query: str, *args: object) -> Mapping[str, object] | None:
        """Return at most one row for one parameterized query."""
        ...

    async def execute(self, query: str, *args: object) -> str:
        """Execute one statement without returning rows."""
        ...

    def transaction(self, *, isolation: str, readonly: bool) -> AbstractAsyncContextManager[None]:
        """Open one explicit transaction boundary."""
        ...


class _PoolAcquireContext(Protocol):
    async def __aenter__(self) -> DatabaseConnection:
        """Borrow one connection."""
        ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: object,
    ) -> bool | None:
        """Return the borrowed connection."""
        ...


class DatabasePool(Protocol):
    """Typed pool surface required by standalone Chronos."""

    def acquire(self) -> _PoolAcquireContext:
        """Borrow one connection."""
        ...

    async def fetch(self, query: str, *args: object) -> Sequence[Mapping[str, object]]:
        """Run one query through a borrowed connection."""
        ...

    async def fetchrow(self, query: str, *args: object) -> Mapping[str, object] | None:
        """Run one single-row query through a borrowed connection."""
        ...

    async def close(self) -> None:
        """Close all pool connections."""
        ...


class _AsyncpgModule(Protocol):
    CannotConnectNowError: type[Exception]

    def create_pool(  # noqa: PLR0913 - mirrors the external constructor we call
        self,
        database_url: str,
        *,
        min_size: int,
        max_size: int,
        timeout: float,
        command_timeout: float,
        init: Callable[[DatabaseConnection], Awaitable[None]],
    ) -> Awaitable[DatabasePool]:
        """Create a PostgreSQL pool."""
        ...


_asyncpg = cast("_AsyncpgModule", import_module("asyncpg"))

_CONNECT_ATTEMPTS: Final[int] = 5
_CONNECT_BASE: Final[timedelta] = timedelta(seconds=0.1)
_CONNECT_MAX: Final[timedelta] = timedelta(seconds=2)
_TRANSIENT_CONNECT_ERRORS: Final[tuple[type[Exception], ...]] = (
    ConnectionError,
    TimeoutError,
    _asyncpg.CannotConnectNowError,
)


async def _init_connection(connection: DatabaseConnection) -> None:
    """Decode PostgreSQL JSONB values into Python objects."""
    await connection.set_type_codec(
        "jsonb", encoder=json.dumps, decoder=json.loads, schema="pg_catalog"
    )


async def create_pool(
    database_url: str,
    *,
    min_size: int = 1,
    max_size: int = 10,
    connect_timeout: timedelta = timedelta(seconds=10),
    command_timeout: timedelta = timedelta(seconds=30),
) -> DatabasePool:
    """Open an asyncpg pool with bounded retries for transient startup failures."""

    async def open_pool() -> DatabasePool:
        return await _asyncpg.create_pool(
            database_url,
            min_size=min_size,
            max_size=max_size,
            timeout=connect_timeout.total_seconds(),
            command_timeout=command_timeout.total_seconds(),
            init=_init_connection,
        )

    retrying = AsyncRetrying(
        stop=stop_after_attempt(_CONNECT_ATTEMPTS),
        wait=wait_exponential(
            multiplier=_CONNECT_BASE.total_seconds(),
            max=_CONNECT_MAX.total_seconds(),
        ),
        retry=retry_if_exception_type(_TRANSIENT_CONNECT_ERRORS),
        reraise=True,
    )
    return await retrying(open_pool)


async def close_pool(pool: DatabasePool) -> None:
    """Gracefully close a connection pool."""
    await pool.close()
