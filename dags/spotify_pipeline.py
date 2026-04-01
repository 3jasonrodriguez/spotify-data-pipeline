from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'airflow',
    'retries': 3,
    'retry_delay': timedelta(minutes=5)
}

with DAG(
    dag_id='spotify_pipeline',
    default_args=default_args,
    start_date=datetime(2026, 4, 15),
    schedule_interval='0 6 * * *',  # daily at 6am
    catchup=False
) as dag:
    # tasks go here
    task = PythonOperator(
    task_id='task_name',
    #python_callable=your_function
)
    #[extract_saved_tracks, extract_artist_genres, ingest_streaming_history] >> load_dim_genre >> load_dim_artist >> ...