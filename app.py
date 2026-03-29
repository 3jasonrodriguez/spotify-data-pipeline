import psycopg2
import pandas as pd
import os 
from dotenv import load_dotenv
import streamlit as st
def app():
    load_dotenv()
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
                hours_per_year_query = '''SELECT year, ROUND(SUM(ms_played) / 3600000.0, 1) as hours_played
                    FROM fact_play_event f INNER JOIN dim_date d on f.date_key=d.dim_date_key
                    GROUP BY year'''
                hours_per_year_df = pd.read_sql(hours_per_year_query, conn)
                st.title("My Spotify Analytics")
                st.header("Hours Listened Per Year")
                st.bar_chart(hours_per_year_df.set_index('year'))

                ten_most_played_songs_query = '''with plays as 
                    (SELECT artist_name, track_name, count(*) as play_counts
                    FROM fact_play_event f INNER JOIN dim_track t on f.track_key=t.track_key inner join dim_artist a on f.artist_key=a.artist_key
                    GROUP BY artist_name, track_name)
                SELECT artist_name, track_name, play_counts
                FROM plays
                ORDER BY play_counts DESC
                LIMIT 10'''
                ten_most_played_songs_query_df = pd.read_sql(ten_most_played_songs_query, conn)
                st.dataframe(ten_most_played_songs_query_df)

    except psycopg2.Error as e:
        print(f"Postgres error: {e}")
        #Rollback on failure
        conn.rollback()

def main():
    a = app()
if __name__ == "__main__":
    main()
