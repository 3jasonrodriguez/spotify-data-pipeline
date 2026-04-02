from airflow import DAG
from airflow.decorators import dag, task
from airflow.operators.python import PythonOperator
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



default_args = {
    'owner': 'airflow',
    'retries': 3,
    'retry_delay': timedelta(minutes=5)
}

with DAG(
    dag_id='spotify_pipeline',
    default_args=default_args,
    start_date=datetime(2026, 4, 15),
    schedule='0 6 * * *',  # daily at 6am
    catchup=False
) as dag:
    # tasks go here
    extract_saved_tracks_task = PythonOperator(
        task_id='extract_saved_tracks',
        python_callable=get_saved_tracks
    )
    ingest_streaming_history_task = PythonOperator(
        task_id='ingest_streaming_history',
        python_callable=ingest_streaming_history
    )
    extract_artists_genres_task = PythonOperator(
        task_id='extract_artists_genres',
        python_callable=get_artists_genres
    )
    load_dim_genre_task = PythonOperator(
        task_id='load_dim_genre',
        python_callable=load_dim_genre
    )
    load_dim_track_task = PythonOperator(
        task_id='load_dim_track',
        python_callable=load_dim_track
    )
    load_dim_artist_task = PythonOperator(
        task_id='load_dim_artist',
        python_callable=load_dim_artist
    )
    load_dim_date_task = PythonOperator(
        task_id='load_dim_date',
        python_callable=load_dim_date
    )
    load_dim_library_task = PythonOperator(
        task_id='load_dim_library',
        python_callable=load_dim_library
    )
    load_bridge_artist_genre_task = PythonOperator(
        task_id='load_bridge_artist_genre',
        python_callable=load_bridge_artist_genre
    )
    load_fact_play_event_task = PythonOperator(
        task_id='load_fact_play_event',
        python_callable=load_fact_play_event
    )
    [extract_saved_tracks_task, extract_artists_genres_task, ingest_streaming_history_task] >> load_dim_genre_task
    [extract_saved_tracks_task, extract_artists_genres_task, ingest_streaming_history_task] >> load_dim_artist_task
    [extract_saved_tracks_task, extract_artists_genres_task, ingest_streaming_history_task] >> load_dim_track_task
    [extract_saved_tracks_task, extract_artists_genres_task, ingest_streaming_history_task] >> load_dim_date_task

    [load_dim_genre_task, load_dim_artist_task, load_dim_track_task, load_dim_date_task] >> load_dim_library_task
    [load_dim_genre_task, load_dim_artist_task, load_dim_track_task, load_dim_date_task] >> load_bridge_artist_genre_task

    [load_dim_library_task, load_bridge_artist_genre_task] >> load_fact_play_event_task