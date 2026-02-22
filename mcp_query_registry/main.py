from fastmcp import FastMCP

from prompts.audit_review import audit_review
from prompts.data_exploration import data_exploration
from prompts.query_authoring import query_authoring
from prompts.query_discovery import query_discovery
from tools.get_query import get_query
from tools.list_queries import list_queries
from tools.run_query import run_query

mcp = FastMCP("oracle-query-registry")

mcp.tool()(list_queries)
mcp.tool()(get_query)
mcp.tool()(run_query)

mcp.prompt()(query_discovery)
mcp.prompt()(data_exploration)
mcp.prompt()(query_authoring)
mcp.prompt()(audit_review)

if __name__ == "__main__":
    mcp.run()
