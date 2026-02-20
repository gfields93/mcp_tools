from fastmcp import FastMCP

from tools.get_query import get_query
from tools.list_queries import list_queries
from tools.run_query import run_query

mcp = FastMCP("oracle-query-registry")

mcp.tool()(list_queries)
mcp.tool()(get_query)
mcp.tool()(run_query)

if __name__ == "__main__":
    mcp.run()
