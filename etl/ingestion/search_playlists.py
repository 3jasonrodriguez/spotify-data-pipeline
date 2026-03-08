from etl.utils.spotify_auth import get_spotify_access_token
import requests
import json
from requests.exceptions import RequestException, HTTPError

def spotify_searches(search_list, search_type, limit):
    all_results = []
    type_map = {"playlist":"playlists", "artist":"artists", "track":"tracks", "album":"albums"}
    token = get_spotify_access_token()
    search_url = "https://api.spotify.com/v1/search"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json" # Optional: specify expected response format
    }
    for query in search_list:
        payload = {
                'q':query, 
                'type':search_type, 
                'limit':limit
        } 
        search_response = requests.get(search_url, headers=headers, params=payload, timeout=10)
        try:
            search_response.raise_for_status()
        except HTTPError as e:
            print(f"HTTP Error: {e}")
            continue
        except RequestException as e:
            print(f"Request failed: {e}")
            continue
        try:
            data = search_response.json()
        except (ValueError, KeyError) as e:
            print(f"Failed to parse JSON for query '{query}': {e}")
            continue
        print(f"result for {query}")
        #items = print(data[(type_map[search_type])]['items'])
        items = data.get(type_map[search_type], {}).get("items", [])
        print(f"Query: {query} -> {len(items)} results")
        #print(items)
        #Append items to master list
        all_results.extend(items)
    # Deduped search results
    unique_results = {p["id"]: p for p in all_results}
    print(f"Total results: {len(all_results)}")
    print(f"Unique results: {len(unique_results)}")
    print(list(unique_results.values()))
    return list(unique_results.values())


#Define main for reusability and importing
def main():
    genre_list = ["prog rock", "progressive rock", "math rock"]
    searches = spotify_searches(genre_list, "playlist", 1)
if __name__ == "__main__":
    main()