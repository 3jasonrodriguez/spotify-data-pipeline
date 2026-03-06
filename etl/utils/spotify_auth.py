import requests
import os
import json
from dotenv import load_dotenv
from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session
from requests.exceptions import RequestException, HTTPError

def get_spotify_access_token ():

    #load variables from .env file
    load_dotenv()
    #Using .env client credentials, grqab an access token
    #For this project, we will simply grab a token for every api call; no need to cache a token or look for an existing one
    token_url = 'https://accounts.spotify.com/api/token'
    client = BackendApplicationClient(client_id=os.getenv("SPOTIFY_CLIENT_ID"))
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    oauth = OAuth2Session(client=client)
    #Try catch for grabbing an access token with exception handling
    try:
        token_response = oauth.fetch_token(token_url=token_url, client_id=client, client_secret=client_secret)
        print(token_response)
        return token_response['access_token']
    except HTTPError as e:
        print(f"HTTP error: {e.token_response['status_code']}")
    except RequestException as e:
        print(f"Connection error: {e}")
    except ValueError:
        print("Invalid JSON response")
        return None


#return access_token