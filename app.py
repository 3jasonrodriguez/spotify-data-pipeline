import psycopg2
import pandas as pd
import os 
from dotenv import load_dotenv
import streamlit as st
import altair as alt
from datetime import datetime, timezone
import sql.streamlit_queries as streamlit_queries

def top_ten_songs(conn):
    query = streamlit_queries.TOP_TEN_SONGS
    df = pd.read_sql(query, conn)
    st.header("Top 10 Most Played Songs")
    #Display data table
    st.dataframe(df, hide_index=True)

def yearly_streaming_hours(conn):
    query = streamlit_queries.HOURS_PER_YEAR
    df = pd.read_sql(query, conn)
    st.header("Hours Listened Per Year")
    #Display bar chart
    st.bar_chart(df.set_index('year'), color="#7DF9FF")  

def genre_trends(conn):
    query = streamlit_queries.GENRE_YEAR_TRENDS
    df = pd.read_sql(query, conn)
    st.header("Yearly Genre Trends")
    #Display data table
    st.dataframe(df, hide_index=True)
    pivot_df = df.pivot(index='year', columns='genre_name', values='hours_played')
    st.line_chart(pivot_df)
def date_streams(conn):
    query = streamlit_queries.DATE_STREAMS
    df = pd.read_sql(query, conn)
    #Aggregate the hours played by date
    day_hours = df.groupby("full_date")["hours_played"].sum().reset_index()
    #Define the selection on click for a date
    selection = alt.selection_point(on="click", fields=['full_date'], name="chart_selection", toggle=True)
    # Create the base altair bar chart for all plays
    streaming_history_chart = alt.Chart(day_hours).mark_bar().encode(
        x="full_date",
        y="hours_played",
        color=alt.condition(
            selection,
            alt.value('#39FF14'),  # Selected bar color
            alt.value('darkgray') # Unselected bar color
        )
    ).add_params(
            selection
    )
    #Display the chart in Streamlit and capture selections
    event_data = st.altair_chart(streaming_history_chart, on_select="rerun",key="my_barchart_selection")
    if event_data and 'selection' in event_data:
        #Grab the selected portion of data to parse
        selection = event_data['selection']
        if selection:
            #For drill down table
            st.subheader("Daily Stream Details:")
            #Parse the selection to grab the selected dates
            chart_selections = [selection[cs] for cs in selection]
            filtered_dates = []
            for obj in chart_selections:
                for attrs in obj:
                    for att in attrs:
                        if att == "full_date":
                            #Convert timestamp back to date
                            ts_ms = attrs[att]
                            converted_date = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc).date()
                            #Account for multiple dates selected in the bar chart
                            filtered_dates.append(converted_date)
            #Filter the dataframe by the selected dates
            filtered_dates_df = df[df["full_date"].isin(filtered_dates)]
            #Show minutes played per song instead of hours
            #Copy before modifying
            filtered_df = filtered_dates_df.copy()
            filtered_df["minutes_played"] = filtered_df["hours_played"] * 60
            filtered_df = filtered_df.drop(columns=['hours_played'])
            #Display the drill down table with filtered data
            st.dataframe(filtered_df, hide_index=True)
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
            #Render the Visualizations
            st.title("My Spotify Analytics")
            top_ten_songs(conn)
            yearly_streaming_hours(conn)
            genre_trends(conn)
            date_streams(conn)
    except psycopg2.Error as e:
        st.error(f"Database error: {e}")
        if conn:
            conn.rollback()

def main():
    a = app()
if __name__ == "__main__":
    main()
