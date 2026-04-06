"""
finviz-mcp : MCP Server exposing finvizfinance as tools for Claude.

Entry point – run with:
    python server.py  (or  mcp dev server.py  for local testing)
"""

from mcp.server.fastmcp import FastMCP
from tools.group import register_group_tools
from tools.screener import register_screener_tools
from tools.quote import register_quote_tools
from tools.insider import register_insider_tools

mcp = FastMCP("finviz")

register_group_tools(mcp)
register_screener_tools(mcp)
register_quote_tools(mcp)
register_insider_tools(mcp)

if __name__ == "__main__":
    mcp.run()
