import streamlit as st
from etl.utils.logger import get_logger
logger = get_logger(__name__)

def home():
    st.set_page_config(layout="wide", page_title="DJ Data")
    st.title("🎧 DJ Data")
    st.write("Your personal Spotify analytics assistant — explore your listening history or ask anything about your music data.")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        with st.container(border=True, height=200):
            st.subheader("📊 Visualizations")
            st.write("Explore your Spotify listening history through custom-built interactive charts and dashboards.")
            st.page_link("pages/1_visualizations.py", label="Open Visualizations →")
    with col2:
        with st.container(border=True, height=200):
            st.subheader("🤖 Ask DJ Data")
            st.write("Ask natural language questions about your Spotify data powered by AI.")
            st.page_link("pages/2_dj_data.py", label="Ask DJ Data →")
    with col3:
        with st.container(border=True, height=200):
            st.subheader("🔍 Discoveries")
            st.write("DJ Data surfaces weekly discoveries from your Spotify listening history — insights you didn't know to look for, powered by AI")
            st.page_link("pages/3_discoveries.py", label="Open Discoveries →")

# top level - outside any function
pg = st.navigation([
    st.Page(home, title="Home", icon=":material/home:"),
    st.Page("pages/1_visualizations.py", title="Visualizations", icon=":material/analytics:"),
    st.Page("pages/2_dj_data.py", title="DJ Data", icon=":material/music_note:"),
    st.Page("pages/3_discoveries.py", title="Discoveries", icon=":material/mystery:"),
])

pg.run()