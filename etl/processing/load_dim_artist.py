import psycopg2
import os
from psycopg2.extras import execute_values
from dotenv import load_dotenv
from etl.processing.athena_utils import run_athena_query

def load_dim_artist():
    load_dotenv()
    artist_query = "SELECT DISTINCT id, name FROM artists"
    #Run athena query
    rows = run_athena_query(artist_query)
    if not rows:
        print(f"No rows returned from the athena query: {artist_query}")
        return
    artist_set = set()
    #Grab the artist id/name and add them to the artist set
    for a in rows[1:]:
        artist_set.add((a.get('Data')[0].get('VarCharValue'), a.get('Data')[1].get('VarCharValue')))
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
                    "INSERT INTO dim_artist (spotify_artist_id, artist_name) VALUES %s ON CONFLICT (spotify_artist_id) DO NOTHING",
                    [(artist[0],artist[1]) for artist in artist_set]
                )
            #Commit the statements
            conn.commit()
            print(f"Loaded {len(artist_set)} artists into dim_artist")
    except psycopg2.Error as e:
        print(f"Postgres error: {e}")
        #Rollback on failure
        conn.rollback()

def main():
    l = load_dim_artist()
if __name__ == "__main__":
    main()
