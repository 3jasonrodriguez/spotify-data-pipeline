import sql.streamlit_queries as streamlit_queries
import pandas as pd
#Grab all current user schemas in postgres
def get_users(conn):
    query = streamlit_queries.GET_USERS
    df = pd.read_sql(query, conn)
    user_list = df['schema_name'].tolist()
    user_list.append("compare")
    return user_list