import psycopg2
import os
from psycopg2.extras import execute_values
from dotenv import load_dotenv
from etl.processing.athena_utils import run_athena_query
from datetime import datetime
from datetime import date
import calendar

def load_dim_date():
    load_dotenv()
    date_query = """SELECT DISTINCT 
    DATE(from_iso8601_timestamp(ts) AT TIME ZONE 'America/New_York') as full_date,
    YEAR(from_iso8601_timestamp(ts) AT TIME ZONE 'America/New_York') as year,
    MONTH(from_iso8601_timestamp(ts) AT TIME ZONE 'America/New_York') as month,
    DAY(from_iso8601_timestamp(ts) AT TIME ZONE 'America/New_York') as day,
    HOUR(from_iso8601_timestamp(ts) AT TIME ZONE 'America/New_York') as hour
FROM streaming_history"""
    #Run athena query
    rows = run_athena_query(date_query)
    if not rows:
        print(f"No rows returned from the athena query: {date_query}")
        return
    dates_set = set()
    #iterate over each row after the headers
    for t in rows[1:]:
        #Grab the track id/name/duration and add them to the artist set
        full_date_str = t.get('Data')[0].get('VarCharValue')
        #convert to date string to date
        full_date = datetime.strptime(full_date_str, "%Y-%m-%d").date()
        year = int(t.get('Data')[1].get('VarCharValue'))
        month = int(t.get('Data')[2].get('VarCharValue'))
        day = int(t.get('Data')[3].get('VarCharValue'))
        hour = int(t.get('Data')[4].get('VarCharValue'))
        is_work_hr = True if hour <=17 and hour >=8 else False
        #Use the date to get the day of week
        dt = date(year, month, day)
        day_of_week = calendar.day_name[dt.weekday()]
        dates_set.add((full_date, is_work_hr, year, month, day, hour, day_of_week))
    conn = None
    try:
        #Open postgres connection
        with psycopg2.connect(
            host=os.getenv("POSTGRES_HOST"),
            port=os.getenv("POSTGRES_PORT"),
            dbname=os.getenv("POSTGRES_DB"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD")
        ) as conn:
            with conn.cursor() as cursor:
                #Parameterize the dates into the insert commands
                results = execute_values(
                    cursor,
                    "INSERT INTO dim_date (full_date, is_work_hour, year, month, day, hour, day_of_week) VALUES %s",
                    [(d[0], d[1], d[2], d[3], d[4], d[5], d[6]) for d in dates_set]
                )
                inserted_count = cursor.rowcount
            #Commit the statements
            conn.commit()
            print(f"Inserted {inserted_count} records into dim_date")
    except psycopg2.Error as e:
        print(f"Postgres error: {e}")
        #Rollback on failure
        conn.rollback()

def main():
    l = load_dim_date()
if __name__ == "__main__":
    main()
