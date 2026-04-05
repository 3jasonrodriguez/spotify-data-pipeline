import psycopg2
import os
import pandas as pd
from psycopg2.extras import execute_values
from dotenv import load_dotenv
from etl.processing.athena_utils import run_athena_query
from etl.utils.connections import get_postgres_conn
from etl.utils.logger import get_logger 
logger = get_logger(__name__)

def load_fact_play_event():    
    load_dotenv()
    fact_query = """SELECT 
        CAST(DATE(from_iso8601_timestamp(ts) AT TIME ZONE 'America/New_York') as VARCHAR) || '_' ||
        CAST(HOUR(from_iso8601_timestamp(ts) AT TIME ZONE 'America/New_York') AS VARCHAR) as full_date_hour,
        SUBSTR(spotify_track_uri, 15) as track_id,
        master_metadata_album_artist_name as artist_name,
        ms_played
    FROM streaming_history
    WHERE spotify_track_uri IS NOT NULL"""
    #Run athena query
    rows = run_athena_query(fact_query)
    if not rows:
        logger.warning(f"No rows returned from the athena query: {fact_query}")
        return
    fact_list = []
    #iterate over each row after the headers
    for r in rows[1:]:
        #extract full date hour composite key
        full_date_hour = r.get('Data')[0].get('VarCharValue')
        #extract track id
        track_id = r.get('Data')[1].get('VarCharValue')
        #extract artist id
        artist_name = r.get('Data')[2].get('VarCharValue')
        #extract ms played
        ms_played = int(r.get('Data')[3].get('VarCharValue'))
        #Add unique combos to a set
        fact_list.append((full_date_hour, track_id, artist_name, ms_played))
    df = pd.DataFrame(fact_list, columns=["full_date_hour", "track_id", "artist_name", "ms_played"])
    conn = None
    try:
        #Open postgres connection
        with get_postgres_conn() as conn:
            with conn.cursor() as cursor:
                #Grab mapping of composite date and hour for dim date keys
                cursor.execute("SELECT CAST(full_date AS VARCHAR) || '_' || CAST (hour AS VARCHAR) AS full_date_hour, dim_date_key FROM dim_date")
                date_mapping = {row[0] : row[1] for row in cursor.fetchall()}
                #Grab mapping of track id to track keys
                cursor.execute("SELECT spotify_track_id, track_key FROM dim_track")
                track_mapping = {row[0]: row[1] for row in cursor.fetchall()}
                #Grab mapping for artist name to artist key
                cursor.execute("SELECT artist_name, artist_key FROM dim_artist")
                artist_mapping = {row[0]: row[1] for row in cursor.fetchall()}
                valid_rows = [(date_mapping.get(row.full_date_hour),track_mapping.get(row.track_id),artist_mapping.get(row.artist_name), row.ms_played) for row in df.itertuples(index=False) 
                              if date_mapping.get(row.full_date_hour) and track_mapping.get(row.track_id) and artist_mapping.get(row.artist_name)]
                #Truncate the table daily. Helps prevent duplicates and keeps fresh data
                cursor.execute("TRUNCATE TABLE fact_play_event")
                #Parameterize the keys, ids, added_at into the insert commands
                execute_values(
                    cursor,
                    "INSERT INTO fact_play_event (date_key, track_key, artist_key, ms_played) VALUES %s",
                    valid_rows
                )
                #Grab table row count after the insert for comparison
                cursor.execute("SELECT count(*) from fact_play_event")
                row_count_after = int(cursor.fetchall()[0][0])
                logger.info(f"Inserted {row_count_after} records into fact_play_event")
            conn.commit()
    except psycopg2.Error as e:
        logger.error(f"Postgres error: {e}")
        #Rollback on failure
        conn.rollback()

def main():
    l = load_fact_play_event()
if __name__ == "__main__":
    main()
