import psycopg2
import pandas as pd
import json
from dotenv import load_dotenv
import streamlit as st
from datetime import datetime, timezone
from etl.utils.streamlit_utils import render_chart, response_generator
from etl.utils.streamlit_connections import get_postgres_conn
from etl.utils.db_utils import get_users
from etl.utils.logger import get_logger 
from agent.orchestrator import ask
logger = get_logger(__name__)
import time


PROMOTED_QUESTIONS_SINGLE = [
    "Who are my top 10 most played artists?",
    "Which artists have I recently discovered in the last year?",
    "How has my average listening session length changed over the years?",
    "Which tracks have I played more than 50 times?",
    "What are my most skipped tracks based on short play times?"
]

PROMOTED_QUESTIONS_COMPARE = [
    "Which artists do both Jason and Kelly listen to the most?",
    "Who discovered new genres first — Jason or Kelly?",
    "Which user has the more diverse music taste by genre count?",
    "How do listening patterns differ from morning, afternoon, and evening across users?",
    "Who has grown their music library faster over the years?",
    "Who tends to listen to songs over and over again more often?"
]

def app():
    st.set_page_config(
        layout="wide"
    )
    st.title("🤖 DJ Data")
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

            # initialize discovery_scope in session state
            if "discovery_scope" not in st.session_state:
                st.session_state.discovery_scope = None

            # use it to set the default radio selection
            default_scope = st.session_state.discovery_scope or "jason"
            st.session_state.discovery_scope = None  # reset after use

            user_scope = st.radio(
                "Query scope",
                options=get_users(conn),
                index=get_users(conn).index(default_scope) if default_scope in get_users(conn) else 0,
                horizontal=True
            )
            #Display promoted questions based on user scope
            cols = st.columns(3)
            questions = PROMOTED_QUESTIONS_COMPARE if user_scope == "compare" else PROMOTED_QUESTIONS_SINGLE

            for i, question in enumerate(questions):
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
                    response_type = ask_response.get("response_type")
                    verdict = ask_response.get("verdict")
                    if response_type == "out_of_scope":
                        st.info("🎵 DJ Data can only answer questions about your personal Spotify listening history. Try asking about your artists, genres, listening habits, or library!")
                    elif response_type == "error":
                        st.error("Something went wrong — please try rephrasing your question.")
                    elif verdict and not verdict.get("passed"):
                        st.warning("⚠️ DJ Data isn't fully confident in this answer — consider rephrasing your question.")
                        st.info("💡 If you used a suggested question, try clicking it again — DJ Data may generate a better query on the next attempt.")
                    else:
                        chart_spec = ask_response.get("chart_spec")
                        text_response = ask_response.get("natural_language_response")
                        raw_data_str = ask_response.get("raw_data")
                        if raw_data_str:
                            raw_data = json.loads(raw_data_str)
                            df = pd.DataFrame(raw_data)
                        else:
                            df = pd.DataFrame()
                        #render chart if there's a spec
                        render_chart(df, chart_spec, text_response)
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
