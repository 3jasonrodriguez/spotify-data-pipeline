import psycopg2
import os
from psycopg2.extras import execute_values
from dotenv import load_dotenv
from etl.processing.athena_utils import run_athena_query
from datetime import datetime
from datetime import date
import calendar
from etl.utils.connections import get_postgres_conn
from etl.utils.logger import get_logger 
logger = get_logger(__name__)

def load_dim_date(user="jason"):
    load_dotenv()
    date_query = f"""SELECT DISTINCT 
        DATE(from_iso8601_timestamp(ts) AT TIME ZONE 'America/New_York') as full_date,
        YEAR(from_iso8601_timestamp(ts) AT TIME ZONE 'America/New_York') as year,
        MONTH(from_iso8601_timestamp(ts) AT TIME ZONE 'America/New_York') as month,
        DAY(from_iso8601_timestamp(ts) AT TIME ZONE 'America/New_York') as day,
        HOUR(from_iso8601_timestamp(ts) AT TIME ZONE 'America/New_York') as hour
    FROM streaming_history
    WHERE user = '{user}'"""
    #Run athena query
    rows = run_athena_query(date_query)
    if not rows:
        logger.warning(f"No rows returned from the athena query: {date_query}")
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
        with get_postgres_conn() as conn:
            with conn.cursor() as cursor:
                #Grab the table row count so we can compare after the insert
                #We are doing the count of inserted records this way because cursor.rowcount is not consistent
                cursor.execute(f"SELECT count(*) from {user}.dim_date")
                row_count_before = int(cursor.fetchall()[0][0])
                #Parameterize the dates into the insert commands
                execute_values(
                    cursor,
                    f"INSERT INTO {user}.dim_date (full_date, is_work_hour, year, month, day, hour, day_of_week) VALUES %s ON CONFLICT (full_date, hour) DO NOTHING",
                    [(d[0], d[1], d[2], d[3], d[4], d[5], d[6]) for d in dates_set]
                )
                #Grab table row count after the insert for comparison
                cursor.execute(f"SELECT count(*) from {user}.dim_date")
                row_count_after = int(cursor.fetchall()[0][0])
                diff_row_count = row_count_after-row_count_before
                logger.info(f"Inserted {diff_row_count} new records into {user}.dim_date")
            conn.commit()
    except psycopg2.Error as e:
        logger.error(f"Postgres error: {e}")
        if conn:
            #Rollback on failure
            conn.rollback()
    finally:
        if conn:
            conn.close()
def main():
    import sys
    user = sys.argv[1] if len(sys.argv) > 1 else "jason"
    load_dim_date(user=user)
if __name__ == "__main__":
    main()
