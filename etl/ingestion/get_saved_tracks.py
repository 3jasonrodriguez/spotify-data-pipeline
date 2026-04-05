import os
from dotenv import load_dotenv
import math
from etl.ingestion.load_to_s3 import load_to_s3
from etl.utils.spotify_auth import get_spotify_access_token
from etl.utils.connections import get_aws_client
import requests
from requests.exceptions import RequestException, HTTPError
from etl.utils.logger import get_logger 
logger = get_logger(__name__)

#Get all saved tracks  in the user library
def get_saved_tracks():
    load_dotenv()
    #Grab token
    token = get_spotify_access_token()
    #Set limit param
    params = {
        'limit':50,
    }
    headers = {
        'Authorization': f"Bearer {token}"
    }
    saved_list = []
    saved_url = "https://api.spotify.com/v1/me/tracks"
    print("Page 1")
    page = 1
    try:
        #Gets initial results for tracks
        saved_response = requests.get(saved_url, headers=headers, params=params)
        saved_response.raise_for_status()
        data = saved_response.json()
        #Extend list of items(tracks)
        saved_list.extend(data.get('items',[]))
        #Grab total count of tracks
        total_saved = data.get('total')
        #Grab total pages (iterations) we expect for logger
        total_pages = math.ceil(total_saved / (params.get('limit')))
        logger.debug(f"Expecting {total_pages} pages")
        #Grab the next url for the next page
        saved_url = data.get('next')
    #Set the next url to none if the initial request fails
    except HTTPError as e:
        logger.error(f"HTTP error: {e}")
        saved_url = None
    except RequestException as e:
        logger.error(f"Connection error: {e}")
        saved_url = None
    except ValueError:
        logger.error("Invalid JSON response")
        saved_url = None
    #While there is a next page url, get the next page
    while saved_url:
        try:
            next_response = requests.get(saved_url, headers=headers)
            next_response.raise_for_status()
            data = next_response.json()
            #Extend list of items(tracks)
            saved_list.extend(data.get('items',[]))
            #Page counter for logger
            page += 1
            logger.debug(f"Page: {page}")
            #Grab the next url for the next page
            saved_url = data.get('next')
        #For a failed page, break the while loop and set the next url to None
        except HTTPError as e:
            logger.error(f"HTTP error: {e}")
            saved_url = None
            break
        except RequestException as e:
            logger.error(f"Connection error: {e}")
            saved_url = None
            break
        except ValueError:
            logger.error("Invalid JSON response")
            saved_url = None
            break
    logger.debug(f"Retrieved {len(saved_list)} saved tracks") 
    load_to_s3(saved_list, "saved_tracks")


def main():
    s = get_saved_tracks()
if __name__ == "__main__":
    main()