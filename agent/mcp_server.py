from mcp.server.fastmcp import FastMCP
import agent.schema_context as context
import psycopg2
import json
from datetime import date, datetime
from decimal import Decimal
import re
from etl.utils.connections import get_postgres_conn
from etl.utils.logger import get_logger 
logger = get_logger(__name__)
#SQL commands to be prohibited
DESTRUCTIVE_KEYWORDS = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'TRUNCATE']

# your schema context and db connection
mcp = FastMCP("spotify-analytics")

@mcp.tool()
def execute_sql(query: str) -> str:
    """Execute a SQL query against the Spotify analytics database."""
    conn = None
    #Check for prohibited SQL commands
    pattern = "|".join(map(re.escape, DESTRUCTIVE_KEYWORDS))
    matches = re.findall(pattern, query, re.IGNORECASE)
    if matches:
        logger.warning(f"Blocked destructive SQL attempt: {query}")
        return "Error: Query blocked — destructive SQL keywords are not permitted."

    #Serialize the raw data output to handle the data types coming from postgres
    def default_serializer(obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, Decimal):
            return float(obj)
        raise TypeError(f"Type {type(obj)} not serializable")
    
    try:
        with get_postgres_conn() as conn:
            with conn.cursor() as cursor:
                # run the query
                cursor.execute(query)
                results = cursor.fetchall()
                # zip results into a dict
                columns = [desc[0] for desc in cursor.description]
                result = [dict(zip(columns, row)) for row in results]
                # truncate to 500 rows max before sending to LLM
                if len(result) > 500:
                    result = result[:500]
                return json.dumps(result, default=default_serializer)
    except psycopg2.Error as e:
        logger.error(f"Postgres error: {e}")
        return f"Error executing query: {str(e)}"
    finally:
        if conn:
            conn.close()
            # return results as a string