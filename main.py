import streamlit as st
from etl.utils.logger import get_logger
logger = get_logger(__name__)

def home():
    st.title("🎧 DJ Data")
    st.write("Your personal Spotify analytics assistant — explore your listening history or ask anything about your music data.")
    
    col1, col2 = st.columns(2)
    with col1:
        with st.container(border=True):
            st.subheader("📊 Visualizations")
            st.write("Explore your Spotify listening history through custom-built interactive charts and dashboards.")
            st.page_link("pages/1_visualizations.py", label="Open Visualizations →")
    with col2:
        with st.container(border=True):
            st.subheader("🤖 Ask DJ Data")
            st.write("Ask natural language questions about your Spotify data powered by AI.")
            st.page_link("pages/2_dj_data.py", label="Ask DJ Data →")

# top level - outside any function
pg = st.navigation([
    st.Page(home, title="Home", icon=":material/home:"),
    st.Page("pages/1_visualizations.py", title="Visualizations", icon=":material/analytics:"),
    st.Page("pages/2_dj_data.py", title="DJ Data", icon=":material/music_note:"),
])

pg.run()