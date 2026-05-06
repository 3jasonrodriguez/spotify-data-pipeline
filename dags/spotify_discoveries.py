from airflow.sdk import DAG, Param
from airflow.providers.standard.operators.python import PythonOperator, ShortCircuitOperator
from airflow.task.trigger_rule import TriggerRule
from datetime import datetime, timedelta

import sql.streamlit_queries as streamlit_queries
from etl.utils.db_utils import get_users
from etl.utils.streamlit_connections import get_postgres_conn
from agent.discoveries_prompt import get_discoveries_prompt
from agent.orchestrator 
from etl.utils.logger import get_logger 
logger = get_logger(__name__)

def get_user_scopes():
    with get_postgres_conn as conn:
        user_scopes = get_users(conn)
    return user_scopes
#Grabs all current user schemas in postgres to know which users need to have insights generated for extensibility and modularity
default_args = {
    'owner': 'airflow',
    'retries': 3,
    'retry_delay': timedelta(minutes=5)
}

with DAG(
    dag_id='spotify_discoveries',
    default_args=default_args,
    start_date=datetime(2026, 1, 1),
    schedule='0 6 * * 0',  # daily at 6am
    catchup=False,
    params={
        "user_scope": Param(default="jason", type="string"),
        "ingest_streaming_history": Param(default=False, type="boolean")
    }
) as dag:
    # tasks go here
