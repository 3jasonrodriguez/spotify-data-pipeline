from airflow.sdk import DAG
from airflow.providers.standard.operators.python import PythonOperator
from agent.orchestrator import discover
from datetime import datetime, timedelta
from etl.utils.logger import get_logger 
logger = get_logger(__name__)

#Define user scopes
USER_SCOPES = ["jason", "kelly", "compare"]
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
            python_callable=discover,
            op_kwargs={"user_scope": scope},
            retries=2,
            retry_delay=timedelta(seconds=30),
        )
        discovery_tasks.append(task)

    #Chain the discovery tasks sequentially
    for i in range(len(discovery_tasks) - 1):
        discovery_tasks[i] >> discovery_tasks[i + 1]