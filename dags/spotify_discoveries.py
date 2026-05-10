from airflow.sdk import DAG
from airflow.providers.standard.operators.python import PythonOperator
from agent.orchestrator import discover
import time
from datetime import datetime, timedelta
from etl.utils.logger import get_logger 
logger = get_logger(__name__)

#Define user scopes
USER_SCOPES = ["jason", "kelly", "compare"]

def run_discovery_with_delay(user_scope: str):
    time.sleep(60)  # wait 60 seconds before each task
    discover(user_scope)

#DAG definition
with DAG(
    dag_id="spotify_discoveries",
    start_date=datetime(2026, 1, 1),
    schedule="@weekly",
    catchup=False,
    tags=["discoveries", "llm"]
) as dag:
    #Grabs all current user schemas in postgres to know which users need to have discoveries generated for extensibility and modularity
    discovery_tasks = []
    for scope in USER_SCOPES:
        task = PythonOperator(
            task_id=f"generate_{scope.lower().replace(' ', '_')}_discovery",
            python_callable=run_discovery_with_delay,
            op_kwargs={"user_scope": scope},
            retries=2,
            retry_delay=timedelta(minutes=2),
        )
        discovery_tasks.append(task)

    #Chain the discovery tasks sequentially
    for i in range(len(discovery_tasks) - 1):
        discovery_tasks[i] >> discovery_tasks[i + 1]