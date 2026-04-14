
from mcp.server.fastmcp import FastMCP
import mcp.schema_context as context
import psycopg2
from psycopg2.extras import execute_values
from etl.utils.connections import get_postgres_conn
from etl.utils.logger import get_logger 
logger = get_logger(__name__)
# your schema context and db connection
mcp = FastMCP("spotify-analytics")

@mcp.tool()
def execute_sql(query: str) -> str:
    """
    Execute a SQL query against the Spotify analytics database.
    
    Schema context:
    {context.SCHEMA_CONTEXT}
    """
    # connect to postgres
    conn = None
    try:
        with get_postgres_conn() as conn:
            with conn.cursor() as cursor:
        # run the query
                cursor.execute(query)
                results = cursor.fetchall()
                
                return 
    except psycopg2.Error as e:
        logger.error(f"Postgres error: {e}")

    finally:
        if conn:
            conn.close()
            # return results as a string