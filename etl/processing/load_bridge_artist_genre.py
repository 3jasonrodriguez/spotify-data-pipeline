import psycopg2
import os
from psycopg2.extras import execute_values
from dotenv import load_dotenv
from etl.processing.athena_utils import run_athena_query
from etl.utils.connections import get_postgres_conn
import pandas as pd
from etl.utils.logger import get_logger 
logger = get_logger(__name__)

def load_bridge_artist_genre(user="jason"):
    load_dotenv()
    bridge_query = f"""SELECT a.name, tag
    FROM artists a
    CROSS JOIN UNNEST(tags) AS t(tag)
    WHERE tag IS NOT NULL 
    AND user = '{user}'"""
    #Run athena query
    rows = run_athena_query(bridge_query)
    if not rows:
        logger.debug(f"No rows returned from the athena query: {bridge_query}")
        return
    bridge_set = set()
    #iterate over each row after the headers
    for t in rows[1:]:
        #Grab the track id/added_at attributes
        artist_name = t.get('Data')[0].get('VarCharValue')
        #convert to date string to date
        genre_name = t.get('Data')[1].get('VarCharValue')
        #Add unique combos to a set
        bridge_set.add((artist_name, genre_name))
    df = pd.DataFrame(list(bridge_set), columns=["artist_name", "genre_name"])
    conn = None
    try:
        #Open postgres connection
        with get_postgres_conn() as conn:
            with conn.cursor() as cursor:
                #Grab the table row count so we can compare after the insert
                #We are doing the count of inserted records this way because cursor.rowcount is not consistent
                cursor.execute(f"SELECT count(*) from {user}.bridge_artist_genre")
                row_count_before = int(cursor.fetchall()[0][0])
                #Grab mapping of track ids and track keys
                cursor.execute(f"SELECT DISTINCT artist_name, artist_key  FROM {user}.dim_artist")
                artist_mapping = {row[0]: row[1] for row in cursor.fetchall()}
                cursor.execute(f"SELECT DISTINCT genre_name, genre_key FROM {user}.dim_genre")
                genre_mapping = {row[0]: row[1] for row in cursor.fetchall()}
                # check how many rows pass the filter
                valid_rows = [(artist_mapping.get(row.artist_name), genre_mapping.get(row.genre_name)) 
                            for row in df.itertuples(index=False) 
                            if artist_mapping.get(row.artist_name) and genre_mapping.get(row.genre_name)]
                #Parameterize the keys, ids, added_at into the insert commands
                execute_values(
                    cursor,
                    f"INSERT INTO {user}.bridge_artist_genre (artist_key, genre_key) VALUES %s ON CONFLICT (artist_key, genre_key) DO NOTHING",
                    [(r[0], r[1]) for r in valid_rows]
                )
                #Grab table row count after the insert for comparison
                cursor.execute(f"SELECT count(*) from {user}.bridge_artist_genre")
                row_count_after = int(cursor.fetchall()[0][0])
                diff_row_count = row_count_after-row_count_before
                logger.info(f"Inserted {diff_row_count} new records into {user}.bridge_artist_genre")
            conn.commit()
    except psycopg2.Error as e:
        logger.error(f"Postgres error: {e}")
        if conn:
         conn.rollback()
    finally:
        if conn:
            conn.close()
def main():
    import sys
    user = sys.argv[1] if len(sys.argv) > 1 else "jason"
    load_bridge_artist_genre(user=user)
if __name__ == "__main__":
    main()
