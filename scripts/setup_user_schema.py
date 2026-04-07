import psycopg2
from etl.utils.connections import get_postgres_conn
from etl.utils.logger import get_logger 
logger = get_logger(__name__)

#Schema per user
def create_schema(cursor, user):
    cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {user}")
#Create all postgres tables for the user
def create_dim_date(cursor, user):
    cursor.execute(f"""CREATE TABLE IF NOT EXISTS {user}.dim_date (
        dim_date_key SERIAL PRIMARY KEY,
        full_date DATE,
        is_work_hour BOOL,
        year INT,
        month INT,
        day INT,
        hour INT,
        day_of_week VARCHAR(10)
    )""")
    cursor.execute(f"ALTER TABLE {user}.dim_date ADD CONSTRAINT unique_date_hour UNIQUE (full_date, hour)")

def create_dim_track(cursor, user):
    cursor.execute(f"""CREATE TABLE IF NOT EXISTS {user}.dim_track (
        track_key SERIAL PRIMARY KEY,
        spotify_track_id VARCHAR(30),
        track_name VARCHAR(255),
        duration_ms INT
    )""")
    cursor.execute(f"ALTER TABLE {user}.dim_track ADD CONSTRAINT unique_spotify_track_id UNIQUE (spotify_track_id)")

def create_dim_artist(cursor, user):
    cursor.execute(f"""CREATE TABLE IF NOT EXISTS {user}.dim_artist (
    artist_key SERIAL PRIMARY KEY,
    spotify_artist_id VARCHAR(30),
    artist_name VARCHAR(255)
    )""")
    cursor.execute(f"ALTER TABLE {user}.dim_artist ADD CONSTRAINT unique_spotify_artist_id UNIQUE (spotify_artist_id)")
    cursor.execute(f"ALTER TABLE {user}.dim_artist ADD CONSTRAINT unique_artist_name UNIQUE (artist_name)")

def create_dim_genre(cursor, user):
    cursor.execute(f"""CREATE TABLE IF NOT EXISTS {user}.dim_genre (
        genre_key SERIAL PRIMARY KEY,
        genre_name VARCHAR(255)
    )""")
    cursor.execute(f"ALTER TABLE {user}.dim_genre ADD CONSTRAINT unique_genre_name UNIQUE (genre_name)")

def create_dim_library(cursor, user):
    cursor.execute(f"""CREATE TABLE IF NOT EXISTS {user}.dim_library (
    library_key SERIAL PRIMARY KEY,
    track_key INT REFERENCES {user}.dim_track(track_key),
    saved_at TIMESTAMP
    )""")
    cursor.execute(f"ALTER TABLE {user}.dim_library ADD CONSTRAINT unique_library_track UNIQUE (track_key)")

def create_bridge_artist_genre(cursor, user):
    cursor.execute(f"""CREATE TABLE IF NOT EXISTS {user}.bridge_artist_genre (
        artist_key INT REFERENCES {user}.dim_artist(artist_key),
        genre_key INT REFERENCES {user}.dim_genre(genre_key),
        PRIMARY KEY (artist_key, genre_key)
    )""")

def create_fact_play_event(cursor, user):
    cursor.execute(f"""CREATE TABLE IF NOT EXISTS {user}.fact_play_event (
        play_key SERIAL PRIMARY KEY,
        date_key INT REFERENCES {user}.dim_date(dim_date_key),
        track_key INT REFERENCES {user}.dim_track(track_key),
        artist_key INT REFERENCES {user}.dim_artist(artist_key),
        ms_played INT
    );""")
#For cleaning tables if desired
def drop_public_tables(cursor):
    tables = [
        "fact_play_event",
        "bridge_artist_genre",
        "dim_library",
        "dim_date",
        "dim_track",
        "dim_artist",
        "dim_genre"
    ]
    for table in tables:
        cursor.execute(f"DROP TABLE IF EXISTS public.{table} CASCADE")
        logger.info(f"Dropped public.{table}")
#Setup db schema and tables per new user
def setup_user(user, drop_public=False):
    conn = None
    try:
        #Open postgres connection
        with get_postgres_conn() as conn:
            with conn.cursor() as cursor:
                create_schema(cursor, user)
                if drop_public:
                    drop_public_tables(cursor)
                create_dim_date(cursor,user)
                create_dim_track(cursor,user)
                create_dim_artist(cursor,user)
                create_dim_genre(cursor,user)
                create_dim_library(cursor,user)
                create_bridge_artist_genre(cursor,user)
                create_fact_play_event(cursor, user)
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
    drop_public = "--drop-public" in sys.argv
    setup_user(user=user, drop_public=drop_public)
if __name__ == "__main__":
    main()








