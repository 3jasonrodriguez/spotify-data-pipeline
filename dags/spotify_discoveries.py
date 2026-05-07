from airflow.sdk import DAG, Param
from airflow.providers.standard.operators.python import PythonOperator
from agent.orchestrator import discover
from datetime import datetime
from etl.utils.logger import get_logger 
logger = get_logger(__name__)

#Define user scopes
USER_SCOPES = ["jason", "kelly", "all_users"]
#DAG definition
with DAG(
    dag_id="discoveries_dag",
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
            op_kwargs={"user_scope": scope}
        )
        discovery_tasks.append(task)

    #Chain the discovery tasks sequentially
    for i in range(len(discovery_tasks) - 1):
        discovery_tasks[i] >> discovery_tasks[i + 1]