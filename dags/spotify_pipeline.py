from airflow import DAG
from airflow.decorators import dag, task
from airflow.operators.python import PythonOperator
from airflow.models.param import Param
from airflow.operators.python import ShortCircuitOperator
from airflow.utils.trigger_rule import TriggerRule
from datetime import datetime, timedelta
from etl.ingestion.get_artists_genres import get_artists_genres
from etl.ingestion.get_saved_tracks import get_saved_tracks
from etl.ingestion.ingest_streaming_history import ingest_streaming_history
from etl.processing.load_dim_artist import load_dim_artist
from etl.processing.load_dim_genre import load_dim_genre
from etl.processing.load_bridge_artist_genre import load_bridge_artist_genre
from etl.processing.load_dim_date import load_dim_date
from etl.processing.load_dim_library import load_dim_library
from etl.processing.load_dim_track import load_dim_track
from etl.processing.load_fact_play_event import load_fact_play_event
from etl.utils.logger import get_logger 
logger = get_logger(__name__)

default_args = {
    'owner': 'airflow',
    'retries': 3,
    'retry_delay': timedelta(minutes=5)
}

with DAG(
    dag_id='spotify_pipeline',
    default_args=default_args,
    start_date=datetime(2026, 1, 1),
    schedule='0 6 * * *',  # daily at 6am
    catchup=False,
    params={
        "user": Param(default="jason", type="string"),
        "ingest_streaming_history": Param(default=False, type="boolean"),    
        "extract_only": Param(default=False, type="boolean"),
        "load_only": Param(default=False, type="boolean")
    }
) as dag:
    # tasks go here
    extract_saved_tracks_task = PythonOperator(
        task_id='extract_saved_tracks',
        python_callable=get_saved_tracks,
        op_kwargs={"user": "{{ params.user }}"}
    )
    ingest_streaming_history_task = PythonOperator(
        task_id='ingest_streaming_history',
        python_callable=ingest_streaming_history,
        op_kwargs={"user": "{{ params.user }}"}
    )
    extract_artists_genres_task = PythonOperator(
        task_id='extract_artists_genres',
        python_callable=get_artists_genres,
        op_kwargs={"user": "{{ params.user }}"}
    )
    load_dim_genre_task = PythonOperator(
        task_id='load_dim_genre',
        python_callable=load_dim_genre,
        op_kwargs={"user": "{{ params.user }}"}
    )
    load_dim_track_task = PythonOperator(
        task_id='load_dim_track',
        python_callable=load_dim_track,
        op_kwargs={"user": "{{ params.user }}"}
    )
    load_dim_artist_task = PythonOperator(
        task_id='load_dim_artist',
        python_callable=load_dim_artist,
        op_kwargs={"user": "{{ params.user }}"}
    )
    load_dim_date_task = PythonOperator(
        task_id='load_dim_date',
        python_callable=load_dim_date,
        op_kwargs={"user": "{{ params.user }}"}
    )
    load_dim_library_task = PythonOperator(
        task_id='load_dim_library',
        python_callable=load_dim_library,
        op_kwargs={"user": "{{ params.user }}"}
    )
    load_bridge_artist_genre_task = PythonOperator(
        task_id='load_bridge_artist_genre',
        python_callable=load_bridge_artist_genre,
        op_kwargs={"user": "{{ params.user }}"}
    )
    load_fact_play_event_task = PythonOperator(
        task_id='load_fact_play_event',
        python_callable=load_fact_play_event,
        op_kwargs={"user": "{{ params.user }}"}
    )
    #Used for determining whether to ingest the streaming history, extract to s3 only, or load to postgres only
    def should_ingest_streaming(**context):
        return context["params"]["ingest_streaming_history"]
    def should_extract(**context):
        return not context["params"]["load_only"]
    def should_load(**context):
        extract_only = context["params"]["extract_only"]
        logger.info(f"extract_only value: {extract_only}, type: {type(extract_only)}")
        return not extract_only
    check_extract_task = ShortCircuitOperator(
        task_id='check_extract',
        python_callable=should_extract,
        ignore_downstream_trigger_rules=False
    )

    check_load_task = ShortCircuitOperator(
        task_id='check_load',
        python_callable=should_load,
        ignore_downstream_trigger_rules=False,
        trigger_rule=TriggerRule.ALL_DONE
    )

    check_streaming_history_task = ShortCircuitOperator(
        task_id='check_streaming_history',
        python_callable=should_ingest_streaming,
        ignore_downstream_trigger_rules=False,
        trigger_rule=TriggerRule.NONE_FAILED
    )
        
    check_extract_task >> extract_saved_tracks_task
    check_extract_task >> check_streaming_history_task >> ingest_streaming_history_task
    extract_saved_tracks_task >> extract_artists_genres_task

    [extract_saved_tracks_task, extract_artists_genres_task, check_streaming_history_task] >> check_load_task    
    check_load_task >> load_dim_genre_task
    check_load_task >> load_dim_artist_task
    check_load_task >> load_dim_track_task
    check_load_task >> load_dim_date_task

    [load_dim_genre_task, load_dim_artist_task, load_dim_track_task, load_dim_date_task] >> load_dim_library_task
    [load_dim_genre_task, load_dim_artist_task, load_dim_track_task, load_dim_date_task] >> load_bridge_artist_genre_task
    [load_dim_library_task, load_bridge_artist_genre_task] >> load_fact_play_event_task