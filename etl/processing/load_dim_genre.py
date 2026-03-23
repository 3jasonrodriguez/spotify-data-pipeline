import psycopg2
import os
from psycopg2.extras import execute_values
from dotenv import load_dotenv
from etl.processing.athena_utils import run_athena_query

def load_dim_genre():
    load_dotenv()
    genre_query = "SELECT DISTINCT tag FROM artists CROSS JOIN UNNEST(tags) AS t(tag) WHERE tag IS NOT NULL"
    #Run athena query
    rows = run_athena_query(genre_query)
    if not rows:
        print(f"No rows returned from the athena query: {genre_query}")
        return
    genre_set = set()
    #Grab the genres and add them to the genre set
    for r in rows[1:]:
        genre = r['Data'][0].get('VarCharValue')
        genre_set.add(genre)
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
                    "INSERT INTO dim_genre (genre_name) VALUES %s ON CONFLICT DO NOTHING",
                    [(genre,) for genre in genre_set]
                )
            #Commit the statements
            conn.commit()
            print(f"Loaded {len(genre_set)} genres into dim_genre")
    except psycopg2.Error as e:
        print(f"Postgres error: {e}")
        #Rollback on failure
        conn.rollback()

def main():
    l = load_dim_genre()
if __name__ == "__main__":
    main()
