import psycopg2
import os
from psycopg2.extras import execute_values
from dotenv import load_dotenv
from etl.processing.athena_utils import run_athena_query
from datetime import datetime
from datetime import date
import calendar
import pandas as pd

def load_dim_library():
    load_dotenv()
    lib_query = """SELECT DISTINCT track.id, added_at
    FROM saved_tracks"""
    #Run athena query
    rows = run_athena_query(lib_query)
    if not rows:
        print(f"No rows returned from the athena query: {lib_query}")
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
        with psycopg2.connect(
            host=os.getenv("POSTGRES_HOST"),
            port=os.getenv("POSTGRES_PORT"),
            dbname=os.getenv("POSTGRES_DB"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD")
        ) as conn:
            with conn.cursor() as cursor:
                #Grab mapping of track ids and track keys
                cursor.execute("SELECT spotify_track_id, track_key FROM dim_track")
                track_mapping = {row[0]: row[1] for row in cursor.fetchall()}
                valid_rows = [(track_mapping.get(row.track_id), row.added_at) for row in df.itertuples(index=False) if track_mapping.get(row.track_id)]
                #Parameterize the keys, ids, added_at into the insert commands
                results = execute_values(
                    cursor,
                    "INSERT INTO dim_library (track_key, saved_at) VALUES %s ON CONFLICT (track_key) DO NOTHING",
                    [(r[0], r[1]) for r in valid_rows]
                )
                inserted_count = cursor.rowcount
            #Commit the statements
            conn.commit()
            print(f"Inserted {inserted_count} records into dim_library")
    except psycopg2.Error as e:
        print(f"Postgres error: {e}")
        #Rollback on failure
        conn.rollback()


def main():
    l = load_dim_library()
if __name__ == "__main__":
    main()
