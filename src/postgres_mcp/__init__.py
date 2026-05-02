import asyncio
import logging
import os
import sys

from . import server
from . import top_queries


def main():
    """Main entry point for the package."""
    # MCP stdio uses stdout for protocol; logs must go to stderr.
    logging.basicConfig(
        level=os.environ.get("POSTGRES_MCP_LOG_LEVEL", "INFO").upper(),
        stream=sys.stderr,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    # As of version 3.3.0 Psycopg on Windows is not compatible with the default
    # ProactorEventLoop.
    # See: https://www.psycopg.org/psycopg3/docs/advanced/async.html#async
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    asyncio.run(server.main())


# Optionally expose other important items at package level
__all__ = [
    "main",
    "server",
    "top_queries",
]
