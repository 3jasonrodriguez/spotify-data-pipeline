import psycopg2
import pandas as pd
import ast
import os 
import json
from dotenv import load_dotenv
import streamlit as st
import altair as alt
from datetime import datetime, timezone
import matplotlib.pyplot as plt
import sql.streamlit_queries as streamlit_queries
from etl.utils.streamlit_connections import get_postgres_conn
from etl.utils.logger import get_logger 
from agent.orchestrator import ask
logger = get_logger(__name__)
import time
PROMOTED_QUESTIONS = [
    "Who are my top 10 most played artists?",
    "What is my listening history over time by genre?",
    "What are my top 10 tracks played during work hours?",
    "What is my total listening time per year?",
    "What saved library tracks have I never played?",
    "What is my longest consecutive listening streak by track?"
]

GENRE_DENYLIST = [
    'http', 'www', '.com', '/', '::',
    'pedophilia', 'lesbian', 'cousin',
    'vaccine', 'porn', 'sex'
]

TYPE_MAP = {
    "quantitative": "Q",
    "ordinal": "O", 
    "temporal": "T"
}

#Used for gradually showing the response from the agent
def response_generator(response):
    for word in response.split():
        yield word + " "
        time.sleep(0.05)

def get_users(conn):
    query = streamlit_queries.GET_USERS
    df = pd.read_sql(query, conn)
    user_list = df['schema_name'].tolist()
    user_list.append("All Users")
    return user_list

def render_bar_chart(df, spec):
    if spec.get('title'):
        st.subheader(spec.get('title'))
    x_type = TYPE_MAP.get(spec.get('x_type'), 'N')
    y_type = TYPE_MAP.get(spec.get('y_type'), 'Q')
    chart = alt.Chart(df).mark_bar().encode(
        x=alt.X(f"{spec.get('x')}:{x_type}", title=spec.get("x")),
        y=alt.Y(f"{spec.get('y')}:{y_type}", title=spec.get("y")),
        color=alt.Color(f"{spec.get('color')}:N") if spec.get('color') else alt.value('#7DF9FF')
    ).properties(title=spec.get('title'), height=400)
    st.altair_chart(chart, use_container_width=True)  # this line is missing

def render_line_chart(df, spec):
    if spec.get('title'):
        st.subheader(spec.get('title'))
    x_type = TYPE_MAP.get(spec.get('x_type'), 'N')
    y_type = TYPE_MAP.get(spec.get('y_type'), 'Q')
    chart = alt.Chart(df).mark_line().encode(
        x=alt.X(f"{spec.get('x')}:{x_type}", title=spec.get("x")),
        y=alt.Y(f"{spec.get('y')}:{y_type}", title=spec.get("y")),
        color=alt.Color(f"{spec.get('color')}:N") if spec.get('color') else alt.value('#7DF9FF')
    ).properties(title=spec.get('title'), height=400)
    st.altair_chart(chart, use_container_width=True)  # this line is missing

def render_area_chart(df, spec):
    if spec.get('title'):
        st.subheader(spec.get('title'))
    x_type = TYPE_MAP.get(spec.get('x_type'), 'N')
    y_type = TYPE_MAP.get(spec.get('y_type'), 'Q')
    chart = alt.Chart(df).mark_area().encode(
        x=alt.X(f"{spec.get('x')}:{x_type}", title=spec.get("x")),
        y=alt.Y(f"{spec.get('y')}:{y_type}", title=spec.get("y")),
        color=alt.Color(f"{spec.get('color')}:N") if spec.get('color') else alt.value('#7DF9FF')
    ).properties(title=spec.get('title'), height=400)
    st.altair_chart(chart, use_container_width=True)

def render_scatter_chart(df, spec):
    if spec.get('title'):
        st.subheader(spec.get('title'))
    x_type = TYPE_MAP.get(spec.get('x_type'), 'N')
    y_type = TYPE_MAP.get(spec.get('y_type'), 'Q')
    chart = alt.Chart(df).mark_point().encode(
        x=alt.X(f"{spec.get('x')}:{x_type}", title=spec.get("x")),
        y=alt.Y(f"{spec.get('y')}:{y_type}", title=spec.get("y")),
        color=alt.Color(f"{spec.get('color')}:N") if spec.get('color') else alt.value('#7DF9FF')
    ).properties(title=spec.get('title'), height=400)
    st.altair_chart(chart, use_container_width=True) 

def render_table(df, spec):
    if spec.get('title'):
        st.subheader(spec.get('title'))
    columns = spec.get('columns')
    valid_columns = [c for c in columns if c in df.columns]
    if valid_columns:
        df = df[valid_columns]

    st.dataframe(df, hide_index=True, use_container_width=True)

def clean_genre_df(df):
    if 'genre_name' not in df.columns:
        return df
    pattern = '|'.join(GENRE_DENYLIST)
    return df[~df['genre_name'].str.contains(pattern, case=False, na=False)]

def app():
    #Render the Visualizations
    st.set_page_config(layout="wide")
    st.title("My Spotify Analytics")
    #query_history is a list that grows as the user asks questions. 
    #current_question lets a promoted button pre-fill the chat input.
    if "query_history" not in st.session_state:
        st.session_state.query_history = []

    if "current_question" not in st.session_state:
        st.session_state.current_question = ""
    load_dotenv()
    conn = None
    try:
        #Open postgres connection
        with get_postgres_conn() as conn:

            user_list_options = get_users(conn)
            #Available user selection
            user_scope = st.radio(
                "Query scope",
                options=get_users(conn),
                horizontal=True
            )
            #Display promoted questions
            cols = st.columns(3)
            for i, question in enumerate(PROMOTED_QUESTIONS):
                if cols[i % 3].button(question, use_container_width=True):
                    st.session_state.current_question = question
                    st.session_state.trigger_ask = True
            # check which input source to use - promoted question or user prompt
            prompt = None
            if st.session_state.get("trigger_ask"):
                prompt = st.session_state.current_question
                st.session_state.trigger_ask = False
            elif chat_prompt := st.chat_input("Ask a question about your Spotify data"):
                prompt = chat_prompt
            #if a user selects a prompt, run the analysis for the prompt
            if prompt:
                st.write(f"Asking: {prompt}")
                with st.spinner("DJ Data is thinking..."):
                    ask_response = ask(prompt, user_scope)
                    print(ask_response)
                    chart_spec = ask_response.get("chart_spec")
                    text_response = ask_response.get("natural_language_response")
                    raw_data_str = ask_response.get("raw_data")
                    if raw_data_str:
                        raw_data = json.loads(raw_data_str)
                        df = pd.DataFrame(raw_data)
                    else:
                        df = pd.DataFrame()
                    #render corresponding chart type
                    if chart_spec and not df.empty:
                        st.write(text_response)
                        chart_type = chart_spec.get("chart_type")
                        if chart_type == "bar":
                            render_bar_chart(df, chart_spec)
                        elif chart_type == "line":
                            render_line_chart(df, chart_spec)
                        elif chart_type == "area":
                            render_area_chart(df, chart_spec)
                        elif chart_type == "scatter":
                            render_scatter_chart(df, chart_spec)
                        elif chart_type == "table":
                            render_table(df, chart_spec)
                    elif df.empty:
                        st.info("No data found for this question.")
                #Add user's question to the query history
                st.session_state.query_history.append(prompt)
                if st.session_state.query_history:
                    st.subheader("Query History")
                    for past_question in reversed(st.session_state.query_history):
                        st.write(f"- {past_question}")
    except psycopg2.Error as e:
        logger.error(f"Database error: {e}")
        st.error(f"Database error: {e}")
        if conn:
            conn.rollback()

def main():
    a = app()
if __name__ == "__main__":
    main()
