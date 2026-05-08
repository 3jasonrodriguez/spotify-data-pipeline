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
    "What is my listening history over time by genre?",
    "What are my top 10 tracks played during work hours?",
    "What is my total listening time per year?",
    "What saved library tracks have I never played?",
    "What is my longest consecutive listening streak by track?"
]

PROMOTED_QUESTIONS_COMPARE = [
    "Who are the top 10 most played artists for both Jason and Kelly?",
    "How does Jason and Kelly's listening history compare over time by genre?",
    "What are the top 10 tracks played during work hours for Jason vs Kelly?",
    "How does Jason and Kelly's total listening time per year compare?",
    "What saved library tracks has neither Jason nor Kelly ever played?",
    "Who has the longest consecutive listening streak — Jason or Kelly?"
]

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

            #Available user selection
            user_scope = st.radio(
                "Query scope",
                options=get_users(conn),
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
                    verdict = ask_response.get("verdict")
                    if verdict and not verdict.get("passed"):
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
