# agent/db_tools.py
import json
import psycopg2
import re
from datetime import date, datetime
from decimal import Decimal
from etl.utils.connections import get_postgres_conn
from etl.utils.logger import get_logger
logger = get_logger(__name__)

DESTRUCTIVE_KEYWORDS = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'TRUNCATE']

def default_serializer(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Type {type(obj)} not serializable")

def execute_sql(query: str) -> str:
    """Execute a SQL query against the Spotify analytics database."""
    pattern = "|".join(map(re.escape, DESTRUCTIVE_KEYWORDS))
    if re.findall(pattern, query, re.IGNORECASE):
        logger.warning(f"Blocked destructive SQL attempt: {query}")
        return "Error: Query blocked — destructive SQL keywords are not permitted."
    try:
        with get_postgres_conn() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                results = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
                result = [dict(zip(columns, row)) for row in results]
                if len(result) > 500:
                    result = result[:500]
                return json.dumps(result, default=default_serializer)
    except psycopg2.Error as e:
        logger.error(f"Postgres error: {e}")
        return f"Error executing query: {str(e)}"