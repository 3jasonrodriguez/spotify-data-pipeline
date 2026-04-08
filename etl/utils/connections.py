from airflow.hooks.base import BaseHook
import json
import psycopg2
import os
from dotenv import load_dotenv
import boto3
from botocore.exceptions import ClientError
from botocore.exceptions import NoCredentialsError  

def get_postgres_conn():
    try:
        connection = BaseHook.get_connection("spotify_postgres")
        return psycopg2.connect(
            host=connection.host,
            port=connection.port,
            dbname=connection.schema,
            user=connection.login,
            password=connection.password
        )
    except Exception:
        load_dotenv()
        return psycopg2.connect(
            host=os.getenv("POSTGRES_HOST"),
            port=os.getenv("POSTGRES_PORT"),
            dbname=os.getenv("POSTGRES_DB"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD")
        )

def get_aws_client(service):
    try:
        aws_conn = BaseHook.get_connection("spotify_aws")
        extra = json.loads(aws_conn.extra)
        return boto3.client(
            service,
            aws_access_key_id=extra["aws_access_key_id"],
            aws_secret_access_key=extra["aws_secret_access_key"],
            region_name=extra["region_name"]
        )
    except Exception:
        load_dotenv()
        return boto3.client(
            service,
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AWS_REGION")
        )
    
def get_spotify_credentials():
    try:
        spotify_conn = BaseHook.get_connection("spotify_api")
        return {
            "client_id": spotify_conn.login,
            "client_secret": spotify_conn.password,
            "refresh_token": json.loads(spotify_conn.extra)["refresh_token"]
        }
    except Exception:
        load_dotenv()
        return {
            "client_id": os.getenv("SPOTIFY_CLIENT_ID"),
            "client_secret": os.getenv("SPOTIFY_CLIENT_SECRET"),
            "refresh_token": os.getenv("SPOTIFY_REFRESH_TOKEN")
        }
    
def get_setup_conn():
    return psycopg2.connect(
        host=os.environ.get("POSTGRES_HOST", "postgres"),
        port=os.environ.get("POSTGRES_PORT", 5432),
        dbname=os.environ.get("POSTGRES_DB", "spotify"),
        user=os.environ.get("POSTGRES_USER", "airflow"),
        password=os.environ.get("POSTGRES_PASSWORD", "airflow")
    )

