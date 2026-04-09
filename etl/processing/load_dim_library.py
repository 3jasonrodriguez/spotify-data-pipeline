import psycopg2
import os
from psycopg2.extras import execute_values
from dotenv import load_dotenv
from etl.processing.athena_utils import run_athena_query
import pandas as pd
from etl.utils.connections import get_postgres_conn
from etl.utils.logger import get_logger 
logger = get_logger(__name__)

def load_dim_library(user="jason"):
    load_dotenv()
    lib_query = f"""SELECT DISTINCT track.id, added_at
    FROM saved_tracks
    WHERE user='{user}'"""
    #Run athena query
    rows = run_athena_query(lib_query)
    if not rows:
        logger.warning(f"No rows returned from the athena query: {lib_query}")
        return
    library_set = set()
    #iterate over each row after the headers
    for t in rows[1:]:
        #Grab the track id/added_at attributes
        track_id = t.get('Data')[0].get('VarCharValue')
        #convert to date string to date
        added_at = t.get('Data')[1].get('VarCharValue')
        #Add unique combos to a set
        library_set.add((track_id, added_at))
    df = pd.DataFrame(list(library_set), columns=["track_id", "added_at"])
    conn = None
    try:
        #Open postgres connection
        with get_postgres_conn() as conn:
            with conn.cursor() as cursor:
                #Grab mapping of track ids and track keys
                cursor.execute(f"SELECT spotify_track_id, track_key FROM {user}.dim_track")
                track_mapping = {row[0]: row[1] for row in cursor.fetchall()}
                valid_rows = [(track_mapping.get(row.track_id), row.added_at) for row in df.itertuples(index=False) if track_mapping.get(row.track_id)]
                #Truncate the table daily. Helps keep the library accurate with what is in the library daily
                cursor.execute(f"TRUNCATE TABLE {user}.dim_library")                
                #Parameterize the keys, ids, added_at into the insert commands
                execute_values(
                    cursor,
                    f"INSERT INTO {user}.dim_library (track_key, saved_at) VALUES %s ON CONFLICT (track_key) DO NOTHING",
                    [(r[0], r[1]) for r in valid_rows]
                )
                #Grab table row count after the insert for comparison
                cursor.execute(f"SELECT count(*) from {user}.dim_library")
                row_count_after = int(cursor.fetchall()[0][0])
                logger.info(f"Inserted {row_count_after} records into {user}.dim_library")
            conn.commit()
    except psycopg2.Error as e:
        logger.error(f"Postgres error: {e}")
        if conn:
            #Rollback on failure
            conn.rollback()
    finally:
        if conn:
            conn.close()

def main():
    import sys
    user = sys.argv[1] if len(sys.argv) > 1 else "jason"
    load_dim_library(user=user)
if __name__ == "__main__":
    main()
