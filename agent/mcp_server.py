from mcp.server.fastmcp import FastMCP
from agent.db_tools import execute_sql
from agent.schema_context import SCHEMA_CONTEXT
from etl.utils.logger import get_logger
logger = get_logger(__name__)

mcp = FastMCP("spotify-analytics")

@mcp.tool()
def execute_sql_tool(query: str) -> str:
    """Execute a SQL query against the Spotify analytics database."""
    return execute_sql(query)