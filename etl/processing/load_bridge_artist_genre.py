import psycopg2
import os
from psycopg2.extras import execute_values
from dotenv import load_dotenv
from etl.processing.athena_utils import run_athena_query
from datetime import datetime
from datetime import date
import calendar
import pandas as pd

def load_bridge_artist_genre():
    load_dotenv()
    bridge_query = """SELECT a.name, tag
    FROM artists a
    CROSS JOIN UNNEST(tags) AS t(tag)
    WHERE tag IS NOT NULL"""
    #Run athena query
    rows = run_athena_query(bridge_query)
    if not rows:
        print(f"No rows returned from the athena query: {bridge_query}")
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
        with psycopg2.connect(
            host=os.getenv("POSTGRES_HOST"),
            port=os.getenv("POSTGRES_PORT"),
            dbname=os.getenv("POSTGRES_DB"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD")
        ) as conn:
            with conn.cursor() as cursor:
                #Grab mapping of track ids and track keys
                cursor.execute("SELECT DISTINCT artist_name, artist_key  FROM dim_artist")
                artist_mapping = {row[0]: row[1] for row in cursor.fetchall()}
                cursor.execute("SELECT DISTINCT genre_name, genre_key FROM dim_genre")
                genre_mapping = {row[0]: row[1] for row in cursor.fetchall()}
                # check how many rows pass the filter
                valid_rows = [(artist_mapping.get(row.artist_name), genre_mapping.get(row.genre_name)) 
                            for row in df.itertuples(index=False) 
                            if artist_mapping.get(row.artist_name) and genre_mapping.get(row.genre_name)]
                #Parameterize the keys, ids, added_at into the insert commands
                execute_values(
                    cursor,
                    "INSERT INTO bridge_artist_genre (artist_key, genre_key) VALUES %s ON CONFLICT (artist_key, genre_key) DO NOTHING",
                    [(r[0], r[1]) for r in valid_rows]
                )
                #Grab rwo count for the insert statement
                inserted_count = cursor.rowcount
            #Commit the statements
            conn.commit()
            print(f"Inserted {inserted_count} records into bridge_artist_genre")
    except psycopg2.Error as e:
        print(f"Postgres error: {e}")
        #Rollback on failure
        conn.rollback()


def main():
    l = load_bridge_artist_genre()
if __name__ == "__main__":
    main()
