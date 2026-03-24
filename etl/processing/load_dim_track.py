import psycopg2
import os
from psycopg2.extras import execute_values
from dotenv import load_dotenv
from etl.processing.athena_utils import run_athena_query

def load_dim_track():
    load_dotenv()
    tracks_query = """ with id_name_hist as (SELECT distinct SUBSTR(spotify_track_uri, 15) as track_id, master_metadata_track_name as track_name
                FROM streaming_history)
                SELECT track_id, track_name, st.track.duration_ms as duration_ms
                FROM id_name_hist hist LEFT JOIN saved_tracks st on hist.track_id=st.track.id
                WHERE hist.track_name IS NOT NULL"""
    #Run athena query
    rows = run_athena_query(tracks_query)
    if not rows:
        print(f"No rows returned from the athena query: {tracks_query}")
        return
    tracks_set = set()
    #iterate over each row after the headers
    for t in rows[1:]:
        #Grab the track id/name/duration and add them to the artist set
        track_id = t.get('Data')[0].get('VarCharValue')
        name = t.get('Data')[1].get('VarCharValue')
        duration = t.get('Data')[2].get('VarCharValue')
        duration = int(duration) if duration else None
        tracks_set.add((track_id, name, duration))
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
                #Parameterize the genres into the insert commands
                results = execute_values(
                    cursor,
                    "INSERT INTO dim_track (spotify_track_id, track_name, duration_ms) VALUES %s ON CONFLICT (spotify_track_id) DO NOTHING",
                    [(track[0], track[1], track[2]) for track in tracks_set]
                )
            #Commit the statements
            conn.commit()
            print(f"Loaded {len(tracks_set)} tracks into dim_track")
    except psycopg2.Error as e:
        print(f"Postgres error: {e}")
        #Rollback on failure
        conn.rollback()

def main():
    l = load_dim_track()
if __name__ == "__main__":
    main()
