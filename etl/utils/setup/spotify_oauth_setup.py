import requests
import os
import json
from dotenv import load_dotenv
from requests.exceptions import RequestException, HTTPError
from urllib.parse import urlencode

#Build out the initial url to manually get the auth code
def get_auth_code_url():
    load_dotenv()
    auth_url = "https://accounts.spotify.com/authorize"
    params = {
        'client_id': os.getenv("SPOTIFY_CLIENT_ID"),
        'response_type':'code',
        'redirect_uri':'http://127.0.0.1:8888/callback', #This redirect uri is configured in the Spotify API Dashboard in the developer account console
        'scope': 'playlist-read-private user-library-read'
    }
    # Build the URL manually using urllib
    from urllib.parse import urlencode
    full_url = f"{auth_url}?{urlencode(params)}"
    print(f"Open this URL in your browser:\n{full_url}")
    return full_url
#Used for obtaining refresh token using the auth code flow
def exchange_code_for_tokens(code):
    load_dotenv()
    auth_url = "https://accounts.spotify.com/api/token"
    payload = {
        'grant_type': 'authorization_code',
        'code':code,
        'redirect_uri':'http://127.0.0.1:8888/callback',
    }
        #Try catch for grabbing an access token with exception handling
    try:
        token_response = requests.post(auth_url, data=payload, auth=(os.getenv("SPOTIFY_CLIENT_ID"), os.getenv("SPOTIFY_CLIENT_SECRET")))
        data = token_response.json()
        refresh_token = data.get('refresh_token')
    except HTTPError as e:
        print(f"HTTP error: {e.token_response['status_code']}")
    except RequestException as e:
        print(f"Connection error: {e}")
    except ValueError:
        print("Invalid JSON response")
    return None