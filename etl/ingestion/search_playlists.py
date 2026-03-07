from etl.utils.spotify_auth import get_spotify_access_token
import requests
import json
from requests.exceptions import RequestException, HTTPError

def spotify_searches(search_list, search_type, limit):
    all_results = []
    type_map = {"playlist":"playlists", "artist":"artists", "track":"tracks"}
    token = get_spotify_access_token()
    search_url = "https://api.spotify.com/v1/search"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json" # Optional: specify expected response format
    }
    for query in search_list:
        payload = {'q':query, 'type':search_type, 'limit':limit} 
        search_response = requests.get(search_url, headers=headers, params=payload)
        data = search_response.json()
        #Append items to master list
        all_results.extend(items)

    return all_results


#Define main for reusability and importing
def main():
    genre_list = ["prog rock", "progressive rock", "math rock"]
    searches = spotify_searches(genre_list, "playlist")
    print(len(searches))
if __name__ == "__main__":
    main()