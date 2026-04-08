import psycopg2
import pandas as pd
import os 
from dotenv import load_dotenv
import streamlit as st
import altair as alt
from datetime import datetime, timezone
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import sql.streamlit_queries as streamlit_queries
from etl.utils.streamlit_connections import get_postgres_conn
from etl.utils.logger import get_logger 
logger = get_logger(__name__)


def get_users(conn):
    query = streamlit_queries.GET_USERS
    df = pd.read_sql(query, conn)
    user_list = df['schema_name'].tolist()
    return user_list

def top_ten_songs(conn, user):
    query = streamlit_queries.TOP_TEN_SONGS.format(user=user)
    df = pd.read_sql(query, conn)
    st.header("Top 10 Most Played Songs")
    #Display data table
    st.dataframe(df, hide_index=True)

def yearly_streaming_hours(conn, user):
    query = streamlit_queries.HOURS_PER_YEAR.format(user=user)
    df = pd.read_sql(query, conn)
    st.header("Annual Streaming Hours")
    #Display bar chart
    st.bar_chart(df.set_index('year'), color="#7DF9FF", x_label="Year", y_label="Hours Listened")  

def listening_streaks(conn, user):
    query = streamlit_queries.LISTENING_STREAK.format(user=user)
    df = pd.read_sql(query, conn)
    st.header("Track Listening Streaks")
    #Display bar chart
    st.dataframe(df, hide_index=True)

def streams_by_day(conn, user):
    query = streamlit_queries.STREAMS_BY_DAY.format(user=user)
    df = pd.read_sql(query, conn)
    st.header("Streams By Day")
    #Display bar chart
    day_order = ["Sunday","Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    #Convert 'day' column to ordered categorical
    df['day_of_week'] = pd.Categorical(df['day_of_week'], categories=day_order, ordered=True)
    #Sort the dataframe based on the categorical order
    df = df.sort_values('day_of_week')
    st.bar_chart(df, color="#7DF9FF", x_label="Day of the Week", y_label="Hours Listened", x="day_of_week", y="hours_played")  

def genre_trends(conn, user):
    query = streamlit_queries.GENRE_YEAR_TRENDS.format(user=user)
    df = pd.read_sql(query, conn)
    st.header("Yearly Genre Trends")
    pivot_df = df.pivot(index='year', columns='genre_name', values='hours_played')
    pivot_df.index = pivot_df.index.astype(str)
    st.line_chart(pivot_df, x_label="Year", y_label="Hours Played")

def generate_word_cloud(text_data):
    #This function expects the text to be split into one string separating the many strings
    # Instantiate and generate the word cloud object
    wordcloud = WordCloud(
        width=700, 
        height=300, 
        background_color="black", 
        colormap='cool',
        max_words=100,
        repeat=False
    ).generate(text_data)
    return wordcloud

def artists_wordcloud(conn, user):
    query = streamlit_queries.ALL_ARTISTS.format(user=user)
    df = pd.read_sql(query, conn)
    st.header("Top Artists")
    text_artists = " ".join(df['artist_name'].astype(str).tolist())
    wc = generate_word_cloud(text_artists)
    # Create a Matplotlib figure
    fig, ax = plt.subplots(figsize=(10, 5), dpi=300)
    ax.imshow(wc, interpolation='bilinear')
    ax.axis("off") # Hide the axes
    st.pyplot(fig) 

def date_streams(conn, user):
    query = streamlit_queries.DATE_STREAMS.format(user=user)
    df = pd.read_sql(query, conn)
    st.header("All Music Streams")
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

def library_adds(conn, user):
    query = streamlit_queries.LIBRARY_ADDS.format(user=user)
    df = pd.read_sql(query, conn)
    st.header("My Library Growth")
    
    saved_dates = df.groupby("saved_at").size().reset_index(name="count")
    
    brush = alt.selection_interval(encodings=['x'])
    
    area = alt.Chart(saved_dates).mark_area(
        line={'color': '#BF40BF'},
        color=alt.Gradient(
            gradient='linear',
            stops=[
                alt.GradientStop(color='white', offset=0),
                alt.GradientStop(color='#BF40BF', offset=1)
            ],
            x1=1, x2=1, y1=1, y2=0
        )
    ).encode(
        x="saved_at:T",
        y="count:Q",
        tooltip=["saved_at:T", "count:Q"],
        opacity=alt.condition(brush, alt.value(1), alt.value(0.3))
    ).add_params(brush)
    
    selected_plot = st.altair_chart(area, on_select="rerun")
    
    if selected_plot and selected_plot.get('selection', {}).get('param_1'):
        selected = selected_plot['selection']['param_1']
        if 'saved_at' in selected:
            date_range = selected['saved_at']
            start = pd.to_datetime(date_range[0], unit='ms')
            end = pd.to_datetime(date_range[1], unit='ms')
            df['saved_at'] = pd.to_datetime(df['saved_at'])
            filtered_df = df[(df['saved_at'] >= start) & (df['saved_at'] <= end)]
            st.subheader("Library Addition Details:")
            st.dataframe(
                filtered_df[['track_name', 'artist_name', 'saved_at']],
                column_config={
                    "track_name": st.column_config.TextColumn("Track"),
                    "artist_name": st.column_config.TextColumn("Artist"),
                    "saved_at": st.column_config.DateColumn("Date Added", format="MMM DD, YYYY")
                },
                hide_index=True,
                use_container_width=True
            )



def app():
    load_dotenv()
    conn = None
    try:
        #Open postgres connection
        with get_postgres_conn() as conn:
            #Render the Visualizations
            st.set_page_config(layout="wide")
            st.title("My Spotify Analytics")
            user_list_options = get_users(conn)
            #Available user selection
            user = st.sidebar.selectbox(
                "Select User",
                options=user_list_options,
                index=0
            )
            date_streams(conn, user)
            genre_trends(conn, user)
            library_adds(conn, user)
            listening_streaks(conn, user)
            streams_by_day(conn, user)
            top_ten_songs(conn, user)
            yearly_streaming_hours(conn, user)
            artists_wordcloud(conn, user)

    except psycopg2.Error as e:
        logger.error(f"Database error: {e}")
        st.error(f"Database error: {e}")
        if conn:
            conn.rollback()

def main():
    a = app()
if __name__ == "__main__":
    main()
