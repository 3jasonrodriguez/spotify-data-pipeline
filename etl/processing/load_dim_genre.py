import psycopg2
import os
from psycopg2.extras import execute_values
from dotenv import load_dotenv
from etl.processing.athena_utils import run_athena_query
from etl.utils.connections import get_postgres_conn
from etl.utils.logger import get_logger 
logger = get_logger(__name__)

def load_dim_genre():
    load_dotenv()
    genre_query = "SELECT DISTINCT tag FROM artists CROSS JOIN UNNEST(tags) AS t(tag) WHERE tag IS NOT NULL"
    #Run athena query
    rows = run_athena_query(genre_query)
    if not rows:
        logger.warning(f"No rows returned from the athena query: {genre_query}")
        return
    genre_set = set()
    #iterate over rows after the headers
    for r in rows[1:]:
        #Grab the genres and add them to the genre set
        genre = r['Data'][0].get('VarCharValue')
        genre_set.add(genre)
    conn = None
    try:
        #Open postgres connection
        with get_postgres_conn() as conn:
            with conn.cursor() as cursor:
                #Grab the table row count so we can compare after the insert
                #We are doing the count of inserted records this way because cursor.rowcount is not consistent
                cursor.execute("SELECT count(*) from dim_genre")
                row_count_before = int(cursor.fetchall()[0][0])
                #Parameterize the genres into the insert commands
                execute_values(
                    cursor,
                    "INSERT INTO dim_genre (genre_name) VALUES %s ON CONFLICT (genre_name) DO NOTHING",
                    [(genre,) for genre in genre_set]
                )
                #Grab table row count after the insert for comparison
                cursor.execute("SELECT count(*) from dim_genre")
                row_count_after = int(cursor.fetchall()[0][0])
                diff_row_count = row_count_after-row_count_before
                logger.info(f"Inserted {diff_row_count} new records into dim_genre")
            conn.commit()
    except psycopg2.Error as e:
        logger.error(f"Postgres error: {e}")
        #Rollback on failure
        conn.rollback()

def main():
    l = load_dim_genre()
if __name__ == "__main__":
    main()
