import os
import time
from dotenv import load_dotenv
import boto3
from botocore.exceptions import ClientError
from botocore.exceptions import NoCredentialsError   
import logging
from etl.utils.logger import get_logger 
logger = get_logger(__name__)
#Pass the string parameter into this function to execute the Athena query and return the results
def run_athena_query(query):
    load_dotenv()
    athena_client = boto3.client(
        "athena",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=os.getenv("AWS_REGION")
    )
    #Rows list will be returned
    rows=[]
    try:
        #Start query execution
        response = athena_client.start_query_execution(
            QueryString=query,
            QueryExecutionContext={"Database": "spotify_pipeline_raw"},
            ResultConfiguration={"OutputLocation": "s3://spotify-pipe-raw-793001767690/athena-results/"}
        )
        #Grab query execution id
        execution_id = response["QueryExecutionId"]
        #Due to the query process being asynchronous, we will be checking its status
        while True:
            #Check the status of the query
            status = athena_client.get_query_execution(
                QueryExecutionId=execution_id
            )["QueryExecution"]["Status"]["State"]
            #Check for specific statuses
            if status in ["SUCCEEDED", "FAILED", "CANCELLED"]:
                #Query failure and break
                if status == "FAILED":
                    logging.error(f"Query failed: {athena_client.get_query_execution(QueryExecutionId=execution_id)['QueryExecution']['Status']['StateChangeReason']}")
                    return None
                break
            time.sleep(1)
        #Grab the response from the query
        response = athena_client.get_query_results(
            QueryExecutionId=execution_id
        )
        #Add the rows from the result
        rows.extend(response['ResultSet']['Rows'])
        #Check for more rows if there are more than 1000 rows
        while 'NextToken' in response:
            response = athena_client.get_query_results(
                QueryExecutionId=execution_id,
                NextToken=response['NextToken']
            )
            #Add more rows
            rows.extend(response['ResultSet']['Rows'])
    except NoCredentialsError:
        logging.error("AWS credentials not found - check your .env file")
        return
    except ClientError as e:
        logging.error(f"Athena query failed: {e}") 
        return 
    #Return rows to be parsed downstream since the structures will be different for different queries
    return rows

def main():
    q = "SELECT DISTINCT tag FROM artists CROSS JOIN UNNEST(tags) AS t(tag) WHERE tag IS NOT NULL"
    aq = run_athena_query(q)
    print(aq)
if __name__ == "__main__":
    main()