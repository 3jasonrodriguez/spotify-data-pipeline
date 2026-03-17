import os
import json
import time
from dotenv import load_dotenv
from datetime import datetime
import requests
from requests.exceptions import RequestException, HTTPError
import boto3
from botocore.exceptions import ClientError
from botocore.exceptions import NoCredentialsError   
from difflib import SequenceMatcher

def names_match(name1, name2, threshold=0.8):
    ratio = SequenceMatcher(None, name1.lower(), name2.lower()).ratio()
    return ratio >= threshold

def get_artists_genres():
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
            Prefix="raw/saved_tracks/",
        )
    except NoCredentialsError:
        print("AWS credentials not found - check your .env file")
    except ClientError as e:
        print(f"S3 data pull failed: {e}")
    #Grab S3 contents containing the keys within the prefix
    partition_contents = partitions.get("Contents", [])
    if not partition_contents:
        print("No partitions found in S3")
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
    tracks_file = None
    try:
        tracks_file = client.get_object(
            Bucket=os.getenv("S3_BUCKET_NAME"),
            Key = f"raw/saved_tracks/year={latest_part[:4]}/month={latest_part[4:6]}/day={latest_part[6:]}/saved_tracks.jsonl"
        )
    except NoCredentialsError:
        print("AWS credentials not found - check your .env file")
        return
    except ClientError as e:
        print(f"S3 data pull failed: {e}")
        return
    #Contents from s3 pull
    tracks_contents = tracks_file["Body"].read().decode("utf-8")
    #Splits the jsonl string into a list of lines, removes trailing newlines, skips empty lines, parses each line into a dict 
    tracks = [json.loads(line) for line in tracks_contents.strip().splitlines() if line]
    #Will hold a list of artist dictionaries
    artists_list = []
    #Go through the track items and navigate to the artists list
    for item in tracks:
        artists = item.get('track', {}).get("artists", {})
        #Some tracks may have a list of artists so we will account for multiple artists or individuals
        if isinstance(artists,list):
            for artist in artists:
                artists_list.append(artist)
        else:
            #Only one artist for the track
            artists_list.append(artists)
    print(f"count in artists list: {len(artists_list)}")
    #Dedup the list of artists by making into a dictionary
    unique_artists = {result['id']:result for result in artists_list if result and result.get('id')}
    print(f"count of unique artists: {len(unique_artists)}")
    #Build out musicbrainz api call for each artist's genre tags - grab genre tags for each artist by artist name query
    for a in unique_artists:
        #Make the tags attribute empty if no tags are found as a match
        unique_artists[a]['tags'] = []
        name = unique_artists[a].get('name')
        musicbrainz_url = f"https://musicbrainz.org/ws/2/artist"
        headers = {
            "User-Agent": f"spotify-data-pipeline/1.0 (3jasonrodriguez@gmail.com)",
        }
        params = {
            'query': name,
            'fmt':'json'
        }
        try:
            #grab search result with exception handling
            time.sleep(2)
            musicbrainz_response = requests.get(musicbrainz_url, headers=headers,params=params, timeout=10) 
            musicbrainz_response.raise_for_status()
            data = musicbrainz_response.json()
            #Grabs artists from the query - there could be multiple
            artists = data.get("artists", [])
            if artists:
                matched_artist = None
                #do a fuzzy match for artist name
                for artist in artists:
                    if names_match(name, artist.get("name", "")):
                        matched_artist = artist
                        break
                if matched_artist:
                    #for a matching artist name, add a tags array for all matched genre tags from musicbrainz
                    unique_artists[a]['tags'] = [ tag.get('name') for tag in matched_artist.get('tags', [])]
        except HTTPError as e:
            print(f"HTTP Error: {e}")
            continue
        except RequestException as e:
            print(f"Request failed: {e}")
            time.sleep(5)
            continue
        #JSON parsing errors
        except (ValueError, KeyError) as e:
            print(f"Failed to parse JSON for items for playlist id:'{id}': {e}")
            continue
        print(unique_artists[a])
    return list(unique_artists.values())
        
def main():
    a = get_artists_genres()
if __name__ == "__main__":
    main()