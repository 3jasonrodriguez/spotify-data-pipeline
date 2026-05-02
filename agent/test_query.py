import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from etl.utils.connections import get_postgres_conn

query = "SELECT * FROM jason.dim_artist LIMIT 5"

conn = None
try:
    conn = get_postgres_conn()
    cursor = conn.cursor()
    cursor.execute(query)
    results = cursor.fetchall()
    col_names = [desc[0] for desc in cursor.description]
    print("Columns:", col_names)
    print("Results:")
    for row in results:
        print(row)
finally:
    if conn:
        conn.close()