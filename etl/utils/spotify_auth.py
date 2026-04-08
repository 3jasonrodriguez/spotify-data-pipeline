import requests
import os
import json
from dotenv import load_dotenv
from requests.exceptions import RequestException, HTTPError
from urllib.parse import urlencode
from etl.utils.connections import get_spotify_credentials
from etl.utils.logger import get_logger 
logger = get_logger(__name__)

#Build out the initial url to manually get the auth code
def get_auth_code_url(user="jason"):
    load_dotenv()
    auth_url = "https://accounts.spotify.com/authorize"
    params = {
        'client_id': os.getenv(f"{user.upper()}_SPOTIFY_CLIENT_ID"),
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
def exchange_code_for_tokens(code, user="jason"):
    load_dotenv()
    auth_url = "https://accounts.spotify.com/api/token"
    payload = {
        'grant_type': 'authorization_code',
        'code':code,
        'redirect_uri':'http://127.0.0.1:8888/callback',
    }
        #Try catch for grabbing an access token with exception handling
    try:
        token_response = requests.post(auth_url, data=payload, auth=(os.getenv(f"{user.upper()}_SPOTIFY_CLIENT_ID"), os.getenv(f"{user.upper()}_SPOTIFY_CLIENT_SECRET")))
        data = token_response.json()
        refresh_token = data.get('refresh_token')
        return refresh_token
    except HTTPError as e:
        logger.error(f"HTTP error: {e.token_response['status_code']}")
    except RequestException as e:
        logger.error(f"Connection error: {e}")
    except ValueError:
        logger.error("Invalid JSON response")
    return None


def get_spotify_access_token (user="jason"):
    #load variables from .env file
    creds = get_spotify_credentials(user)
    auth_url = "https://accounts.spotify.com/api/token"
    payload = {
        'grant_type': 'refresh_token',
        'refresh_token':creds["refresh_token"],
    }
        #Try catch for grabbing an access token with exception handling
    try:
        token_response = requests.post(auth_url, data=payload, auth=(creds["client_id"], creds["client_secret"]))
        data = token_response.json()
        access_token = data.get('access_token')
        return access_token
    except HTTPError as e:
        logger.error(f"HTTP error: {e.token_response['status_code']}")
    except RequestException as e:
        logger.error(f"Connection error: {e}")
    except ValueError:
        logger.error("Invalid JSON response")
    return None

def main():
    #get_auth_code_url("kelly")
    #e = exchange_code_for_tokens("AQAC6dnPilgFWYYcBsb4CTKtLIlRE61-qiVbhtCUhmg08XlKbqmWbmtLN2VQxgLc4JMGg55AbRgMD3-UsakzVaDLhwTzFaMoMSxPXAsk7Vv8TAUslOqbRV0PP8n4A-kMDhMk9sLY2d_dX8i8cfSSFZ3L6UMgvOVh08AoanrUgLMT3nnMPFevWuhYIkt_4_-xrNsJcuJNS32DSAPsu9yRY1RS_q7WezuoKYFyzA","kelly")
    #print(e)
    t = get_spotify_access_token("kelly")
    print(t)
if __name__ == "__main__":
    main()