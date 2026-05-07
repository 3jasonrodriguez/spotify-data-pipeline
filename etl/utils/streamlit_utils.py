import time
import streamlit as st
import altair as alt
from datetime import datetime, timezone
import matplotlib.pyplot as plt
import sql.streamlit_queries as streamlit_queries

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

def render_chart(df, chart_spec, text_response=None):
    df = clean_genre_df(df)
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