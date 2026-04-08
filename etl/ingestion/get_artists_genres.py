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
from etl.ingestion.load_to_s3 import load_to_s3
from etl.utils.connections import get_aws_client
from etl.utils.logger import get_logger 
logger = get_logger(__name__)

def names_match(name1, name2, threshold=0.8):
    ratio = SequenceMatcher(None, name1.lower(), name2.lower()).ratio()
    return ratio >= threshold

def get_artists_genres(user="jason"):
    load_dotenv()
    s3_client = get_aws_client("s3")
    tracks_file = None
    try:
        tracks_file = s3_client.get_object(
            Bucket=os.getenv("S3_BUCKET_NAME"),
            Key = f"raw/saved_tracks/user={user}/saved_tracks.jsonl"
        )
    except NoCredentialsError:
        logger.error("AWS credentials not found - check your .env file")
        return
    except ClientError as e:
        logger.error(f"S3 data pull failed: {e}")
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
    logger.debug(f"count in artists list: {len(artists_list)}")
    #Dedup the list of artists by making into a dictionary
    unique_artists = {result['id']:result for result in artists_list if result and result.get('id')}
    logger.info(f"count of unique artists: {len(unique_artists)}")
    #######################################################################################  
    # Look for already tagged/genre enriched artists to save calls to the musicbrainz api.
    # This is too improve performance rather than making calls for all artists
    #######################################################################################
    already_enriched_ids = set()
    existing_artists_dict = {}    
    existing_artists_file = None
    #Grabbing exisiting artists to find artists that already have genres
    try:
        existing_artists_file = s3_client.get_object(
            Bucket=os.getenv("S3_BUCKET_NAME"),
            Key = f"raw/artists/user={user}/artists.jsonl"
        )
    except NoCredentialsError:
        logger.error("AWS credentials not found - check your .env file")
        return
    except ClientError as e:
        logger.error(f"S3 data pull failed: {e}")
        pass
    #Check if the call for the latest partition succeeds
    if existing_artists_file:
        existing_artists_contents = existing_artists_file["Body"].read().decode("utf-8")
        #Splits the jsonl string into a list of lines, removes trailing newlines, skips empty lines, parses each line into a dict 
        existing_artists = [json.loads(line) for line in existing_artists_contents.strip().splitlines() if line]
        #Dict for the artists already in the artists file structure in s3
        existing_artists_dict = {a["id"]: a for a in existing_artists}
        #Already enriched means we have already done a call to musicbrainz to get tags/genres if available
        already_enriched_ids = set(existing_artists_dict.keys())      
    #Find which artists we have not looked up in musicbrainz 
    unenriched_artists_ids = set(unique_artists.keys()) - already_enriched_ids
    unenriched_artists = {id: unique_artists[id] for id in unenriched_artists_ids}
    #Build out musicbrainz api call for each artist's genre tags - grab genre tags for each artist by artist name query
    for a in unenriched_artists:
        #Make the tags attribute empty if no tags are found as a match
        unenriched_artists[a]['tags'] = []
        name = unenriched_artists[a].get('name')
        logger.debug(f"Enriching {name}")
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
                    unenriched_artists[a]['tags'] = [ tag.get('name') for tag in matched_artist.get('tags', [])]
        except HTTPError as e:
            logger.error(f"HTTP Error: {e}")
            continue
        except RequestException as e:
            logger.error(f"Request failed: {e}")
            time.sleep(5)
            continue
        #JSON parsing errors
        except (ValueError, KeyError) as e:
            logger.error(f"Failed to parse JSON for items for artist id:'{id}': {e}")
            continue
    #Merge all artists after enriching them with the existing enriched artists
    logger.debug(f"Processed enriching {len(unenriched_artists)} with tags/genres")
    all_artists = {**existing_artists_dict, **unenriched_artists}
    load_to_s3(list(all_artists.values()), "artists", user, snapshot=True)
    return list(all_artists.values())
def main():
    import sys
    user = sys.argv[1] if len(sys.argv) > 1 else "jason"
    get_artists_genres(user=user)
if __name__ == "__main__":
    main()