import os
import json
from dotenv import load_dotenv
from datetime import datetime
from etl.utils.spotify_auth import get_spotify_access_token
import requests
from requests.exceptions import RequestException, HTTPError
import boto3
from botocore.exceptions import ClientError
from botocore.exceptions import NoCredentialsError
import logging
from etl.utils.logger import get_logger 
logger = get_logger(__name__)

def get_playlist_tracks():
    load_dotenv()
    #Using creds to for s3 client connect
    client = boto3.client(
        "s3",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=os.getenv("AWS_REGION")
    )
    #Grabbing latest partition in S3
    try:
        partitions = client.list_objects_v2(
            Bucket=os.getenv("S3_BUCKET_NAME"),
            Prefix="raw/playlist/",
        )
    except NoCredentialsError:
        logging.error("AWS credentials not found - check your .env file")
    except ClientError as e:
        logging.error(f"S3 data pull failed: {e}")
    #Grab S3 contents containing the keys within the prefix
    partition_contents = partitions.get("Contents", [])
    if not partition_contents:
        logging.warning("No partitions found in S3")
        return
   #Used to grab all yyyymmdd extracted values to determine the latest
    part_list = []
    #Iterate over all the keys to grab the key paths
    for part in partition_contents:
        filename = part["Key"]
        year = filename.split("year=")[1].split("/")[0]
        month = filename.split("month=")[1].split("/")[0]
        day = filename.split("day=")[1].split("/")[0]
        dt = f"{year}{month}{day}"
        part_list.append(dt)
    #Grab latest partition and make it a datetime object to parse out the year/month/day
    latest_part = max(part_list)
    try:
        playlist_file = client.get_object(
            Bucket=os.getenv("S3_BUCKET_NAME"),
            Key = f"raw/playlist/year={latest_part[:4]}/month={latest_part[4:6]}/day={latest_part[6:]}/playlist.jsonl"
        )
    except NoCredentialsError:
        logging.error("AWS credentials not found - check your .env file")
    except ClientError as e:
        logging.error(f"S3 data pull failed: {e}")
    #Contents from s3 pull
    playlists_contents = playlist_file["Body"].read().decode("utf-8")
    #Splits the jsonl string into a list of lines, removes trailing newlines, skips empty lines, parses each line into a dict 
    playlists = [json.loads(line) for line in playlists_contents.strip().splitlines() if line]
    #Grab playlist ids
    playlist_ids = [p["id"] for p in playlists if p and p.get("id")]
    #Get access token
    token = get_spotify_access_token()
    #For each playlist, grab the tracks
    for id in playlist_ids:
        items_url = f"https://api.spotify.com/v1/playlists/{id}/items"
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json" # Optional: specify expected response format
        }
        payload = {
            'limit':50,
            'market':'US'
        } 
        try:
            #grab search result with exception handling
            items_response = requests.get(items_url, headers=headers, params=payload, timeout=10)
            items_response.raise_for_status()
            data = items_response.json()
        except HTTPError as e:
            logging.error(f"HTTP Error: {e}")
            continue
        except RequestException as e:
            logging.error(f"Request failed: {e}")
            continue
        #JSON parsing errors
        except (ValueError, KeyError) as e:
            logging.error(f"Failed to parse JSON for items for playlist id:'{id}': {e}")
            continue    
def main():
    playlist_tracks = get_playlist_tracks()
if __name__ == "__main__":
    main()