"""AbletonMCP server -- MCP bridge to Ableton Live."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from mcp.server.fastmcp import FastMCP

from MCP_Server.connection import get_ableton_connection, shutdown_connection

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("AbletonMCPServer")


@asynccontextmanager
async def server_lifespan(server: FastMCP) -> AsyncIterator[dict[str, Any]]:
    """Manage Ableton connection lifecycle."""
    try:
        logger.info("AbletonMCP server starting up")

        try:
            get_ableton_connection()
            logger.info("Successfully connected to Ableton on startup")
        except Exception as e:
            logger.warning(f"Could not connect to Ableton on startup: {str(e)}")
            logger.warning("Make sure the Ableton Remote Script is running")

        yield {}
    finally:
        logger.info("Disconnecting from Ableton on shutdown")
        shutdown_connection()
        logger.info("AbletonMCP server shut down")


# Create the MCP server with lifespan support
mcp = FastMCP("AbletonMCP", lifespan=server_lifespan)

# Import tool modules AFTER mcp is created (triggers @mcp.tool() registration)
import MCP_Server.tools  # noqa: E402, F401


def main():
    """Run the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
