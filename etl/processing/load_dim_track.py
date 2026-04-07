import psycopg2
import os
from psycopg2.extras import execute_values
from dotenv import load_dotenv
from etl.processing.athena_utils import run_athena_query
from etl.utils.connections import get_postgres_conn
from etl.utils.logger import get_logger 
logger = get_logger(__name__)

def load_dim_track(user="jason"):
    load_dotenv()
    tracks_query = f"""SELECT DISTINCT track_id, track_name, duration_ms FROM (
        -- tracks from streaming history
        SELECT SUBSTR(spotify_track_uri, 15) as track_id, 
            master_metadata_track_name as track_name,
            NULL as duration_ms
        FROM streaming_history
        WHERE spotify_track_uri IS NOT NULL
        AND user='{user}'
        
        UNION
        
        -- tracks from saved library
        SELECT track.id as track_id,
            track.name as track_name,
            track.duration_ms as duration_ms
        FROM saved_tracks
        WHERE user='{user}'
    )
    WHERE track_id IS NOT NULL 
    AND track_name IS NOT NULL"""
    #Run athena query
    rows = run_athena_query(tracks_query)
    if not rows:
        logger.warning(f"No rows returned from the athena query: {tracks_query}")
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
        with get_postgres_conn() as conn:
            with conn.cursor() as cursor:
                #Grab the table row count so we can compare after the insert
                #We are doing the count of inserted records this way because cursor.rowcount is not consistent
                cursor.execute(f"SELECT count(*) from {user}.dim_track")
                row_count_before = int(cursor.fetchall()[0][0])
                #Parameterize the genres into the insert commands
                execute_values(
                    cursor,
                    f"""INSERT INTO {user}.dim_track (spotify_track_id, track_name, duration_ms) VALUES %s ON CONFLICT (spotify_track_id) DO UPDATE 
                        SET duration_ms = EXCLUDED.duration_ms 
                        WHERE dim_track.duration_ms IS NULL""",
                    [(track[0], track[1], track[2]) for track in tracks_set]
                )
                #Grab table row count after the insert for comparison
                cursor.execute(f"SELECT count(*) from {user}.dim_track")
                row_count_after = int(cursor.fetchall()[0][0])
                diff_row_count = row_count_after-row_count_before
                logger.info(f"Inserted {diff_row_count} new records into {user}.dim_track")
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
    load_dim_track(user=user)
if __name__ == "__main__":
    main()
