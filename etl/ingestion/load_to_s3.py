import os
import json
from dotenv import load_dotenv
from datetime import datetime
import boto3
from botocore.exceptions import ClientError
from botocore.exceptions import NoCredentialsError
#Load playlists seacrh results to s3
def load_to_s3(results_list, entity_type, year=None):
    if not results_list:
        print(f"No records to load for {entity_type}")
        return
    #Load .env
    load_dotenv()
    #If a year is sent (for streaming data), use the yearly partition
    if year:
        s3_key = f"raw/{entity_type}/year={year}/{entity_type}.jsonl"
    else:
        #Build out the s3 key for todays date
        #Grab date partials to build out s3 bucket/partition structure
        today = datetime.now()
        yr = today.strftime("%Y")
        mo = today.strftime("%m")
        dy = today.strftime("%d")
        s3_key = f"raw/{entity_type}/year={yr}/month={mo}/day={dy}/{entity_type}.jsonl"
    #Iterate through each result dictionary
    #lines for loading JSONL to s3
    lines = []
    for result in results_list:
        #Add each result to a the list
        lines.append(json.dumps(result))
    #join resulting lines to jsonl string
    jsonl_string = "\n".join(lines)
    #Using creds to for s3 client connect
    client = boto3.client(
        "s3",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=os.getenv("AWS_REGION")
    )
    #Placing object to s3 bucket
    try:
        client.put_object(
            Bucket=os.getenv("S3_BUCKET_NAME"),
            Key=s3_key,
            Body=jsonl_string.encode("utf-8") # S3 expects bytes, so the jsonl string has to be encoded
        )
        print(f"{s3_key} loaded to S3")
    except NoCredentialsError:
        print("AWS credentials not found - check your .env file")
    except ClientError as e:
        print(f"{s3_key} upload failed: {e}")


def main():
    #genre_list = ["prog rock", "progressive rock", "math rock"]
    #searches = spotify_searches(genre_list, "playlist", 10)
    #load_to_s3(searches, "playlists")
    #saved_tracks = get_saved_tracks()
    #load_to_s3(saved_tracks, "saved_tracks")
    #art_genres = get_artists_genres()
    #load_to_s3(art_genres, "artists")
    print()
if __name__ == "__main__":
    main()