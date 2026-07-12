"""MCP Server: DB+Chain Bridge.

Connects Claude to local databases (SQLite, JSON) and the Monad testnet.
"""

from mcp.server.fastmcp import FastMCP

from src.tools.sqlite_tools import register_sqlite_tools
from src.tools.json_tools import register_json_tools
from src.tools.blockchain_tools import register_blockchain_tools

# Create the FastMCP server instance
mcp = FastMCP("DB+Chain Bridge")

# Register all tool categories
register_sqlite_tools(mcp)
register_json_tools(mcp)
register_blockchain_tools(mcp)


def main():
    """Entry point — runs the server via stdio transport."""
    mcp.run()


if __name__ == "__main__":
    main()
