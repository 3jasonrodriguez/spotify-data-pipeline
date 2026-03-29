import psycopg2
import os
from psycopg2.extras import execute_values
from dotenv import load_dotenv
from etl.processing.athena_utils import run_athena_query

def load_dim_artist():
    load_dotenv()
    #Grabbing artists from saved tracks in the library and streaming history.
    #This grabs all artists even if they aren't in the library 
    artist_query = '''SELECT DISTINCT id, name 
                    FROM artists 
                    union 
                    SELECT DISTINCT NULL, master_metadata_album_artist_name
                    FROM streaming_history
                    WHERE master_metadata_album_artist_name IS NOT NULL'''
    #Run athena query
    rows = run_athena_query(artist_query)
    if not rows:
        print(f"No rows returned from the athena query: {artist_query}")
        return
    artist_set = set()
    #iterate over each row after the headers
    for a in rows[1:]:
        #Grab the artist id/name and add them to the artist set
        artist_id = a.get('Data')[0].get('VarCharValue')
        name = a.get('Data')[1].get('VarCharValue')
        artist_set.add((artist_id, name))
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
                #Grab the table row count so we can compare after the insert
                #We are doing the count of inserted records this way because cursor.rowcount is not consistent
                cursor.execute("SELECT count(*) from dim_artist")
                row_count_before = int(cursor.fetchall()[0][0])
                #Parameterize the genres into the insert commands
                execute_values(
                    cursor,
                    "INSERT INTO dim_artist (spotify_artist_id, artist_name) VALUES %s ON CONFLICT (artist_name) DO NOTHING",
                    [(artist[0],artist[1]) for artist in artist_set]
                )
                #Grab table row count after the insert for comparison
                cursor.execute("SELECT count(*) from dim_artist")
                row_count_after = int(cursor.fetchall()[0][0])
                diff_row_count = row_count_after-row_count_before
                print(f"Inserted {diff_row_count} new records into dim_artist")
            conn.commit()
    except psycopg2.Error as e:
        print(f"Postgres error: {e}")
        #Rollback on failure
        conn.rollback()

def main():
    l = load_dim_artist()
if __name__ == "__main__":
    main()
