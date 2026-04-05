FROM apache/airflow:3.1.8
RUN pip install --no-cache-dir boto3 psycopg2-binary requests python-dotenv pandas pyyaml