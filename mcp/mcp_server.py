
from mcp.server.fastmcp import FastMCP
import mcp.schema_context as context
import psycopg2
from etl.utils.connections import get_postgres_conn
from etl.utils.logger import get_logger 
logger = get_logger(__name__)
# your schema context and db connection
mcp = FastMCP("spotify-analytics")

@mcp.tool()
def execute_sql(query: str) -> str:
    """Execute a SQL query against the Spotify analytics database."""
    conn = None
    try:
        with get_postgres_conn() as conn:
            with conn.cursor() as cursor:
                # run the query
                cursor.execute(query)
                results = cursor.fetchall()
                # zip results into a dict
                columns = [desc[0] for desc in cursor.description]
                return str([dict(zip(columns, row)) for row in results])
    except psycopg2.Error as e:
        logger.error(f"Postgres error: {e}")
        return f"Error executing query: {str(e)}"
    finally:
        if conn:
            conn.close()
            # return results as a string