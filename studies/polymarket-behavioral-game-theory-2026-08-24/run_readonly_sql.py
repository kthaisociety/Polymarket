"""Execute one frozen study SQL source through the proved production read-only role."""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

import asyncpg

from tools.dev.prod_secrets import read_secret


async def execute(source: Path) -> None:
    connection = await asyncpg.connect(
        host="127.0.0.1",
        port=15432,
        user="human_ro",
        password=read_secret("human_ro_password"),
        database="bdl",
        command_timeout=600,
    )
    try:
        async with connection.transaction(isolation="repeatable_read", readonly=True):
            identity = await connection.fetchrow(
                """
                SELECT current_user AS role,
                       current_setting('default_transaction_read_only') AS default_read_only,
                       current_setting('transaction_read_only') AS transaction_read_only
                """
            )
            if identity is None or dict(identity) != {
                "role": "human_ro",
                "default_read_only": "on",
                "transaction_read_only": "on",
            }:
                raise RuntimeError(f"production authority proof failed: {dict(identity or {})}")
            result = await connection.fetchval(source.read_text(encoding="utf-8"))
            print(result)
    finally:
        await connection.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    arguments = parser.parse_args()
    asyncio.run(execute(arguments.source))


if __name__ == "__main__":
    main()
