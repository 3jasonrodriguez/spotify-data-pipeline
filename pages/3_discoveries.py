import psycopg2
import pandas as pd
from dotenv import load_dotenv
import streamlit as st
import sql.streamlit_queries as streamlit_queries
from etl.utils.streamlit_connections import get_postgres_conn
from etl.utils.streamlit_utils import render_chart
from etl.utils.logger import get_logger 
from agent.orchestrator import ask
logger = get_logger(__name__)
import time

def get_discoveries(conn):
    query = streamlit_queries.GET_DISCOVERIES
    df = pd.read_sql(query, conn)
    return df
    #for scope in ["jason", "kelly", "all_users"]:
        #scope_df = df[df["user_scope"] == scope]

def app():
    #Render the Visualizations
    st.set_page_config(layout="wide")
    st.title("Discoveries")
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

            # get discoveries from postgres
            discoveries_df = get_discoveries(conn)

            # top half - jason and kelly side by side
            col1, col2 = st.columns(2)
            for scope, col in [("jason", col1), ("kelly", col2)]:
                with col:
                    # filter df for this scope
                    scope_row = discoveries_df[discoveries_df["user_scope"] == scope]
                    
                    if not scope_row.empty:
                        row = scope_row.iloc[0]
                        
                        with st.container(border=True):
                            st.subheader(f"🎵 {scope.capitalize()}")
                            st.write(row["insight_text"])
                            raw_data_df = pd.DataFrame(row["raw_data"]) if row["raw_data"] else pd.DataFrame()
                            render_chart(raw_data_df, row["chart_spec"])
                            # hint: row["chart_spec"] is a dict from Postgres JSONB
                            
                            # follow-up button
                            if st.button(f"💡 Explore further", key=f"explore_{scope}"):
                                st.session_state.current_question = row["follow_up_question"]
                                st.session_state.trigger_ask = True
                                st.switch_page("pages/2_dj_data.py")
                    else:
                        with st.container(border=True):
                            st.info("No discoveries yet for this user.")
            #Bottom half for all users
            col1 = st.columns(1)
            # fix - full width doesn't need columns at all
            st.divider()  # visual separator
            scope_row = discoveries_df[discoveries_df["user_scope"] == "all_users"]
            if not scope_row.empty:
                row = scope_row.iloc[0]
                with st.container(border=True):
                    st.subheader("🔄 Jason & Kelly")
                    st.write(row["insight_text"])
                    raw_data_df = pd.DataFrame(row["raw_data"]) if row["raw_data"] else pd.DataFrame()
                    render_chart(raw_data_df, row["chart_spec"])
                    if st.button("💡 Explore further", key="explore_all_users"):
                        st.session_state.current_question = row["follow_up_question"]
                        st.session_state.trigger_ask = True
                        st.switch_page("pages/2_dj_data.py")
            else:
                with st.container(border=True):
                    st.info("No discoveries yet for comparison.")
                    

# bottom half - all_users full width
# your turn - follow the same pattern

    except psycopg2.Error as e:
            logger.error(f"Database error: {e}")
            st.error(f"Database error: {e}")
            if conn:
                conn.rollback()

def main():
    a = app()
if __name__ == "__main__":
    main()
