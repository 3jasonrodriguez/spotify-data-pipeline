from etl.utils.spotify_auth import get_spotify_access_token
import requests
from requests.exceptions import RequestException, HTTPError

#Function to iterate over a list of searchable objects in the Spotify search.
#Search_list is a list of the strings for the object type we will search through
#Search types are defined within this function in a map
#Limit is defined for returning results. The max is 50 in the API.
def spotify_searches(search_list, search_type, limit):
    #Used for the "object" type in Spotify that we are searching for. The plural form is used within the nested JSON
    type_map = {"playlist":"playlists", "artist":"artists", "track":"tracks", "album":"albums"}
    if search_type not in type_map:
        raise ValueError(f"Invalid search type: {search_type}")
    #list to collect all search results
    all_results = []

    #Build out search API call
    token = get_spotify_access_token()
    search_url = "https://api.spotify.com/v1/search"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json" # Optional: specify expected response format
    }
    #Iterate over the list of strings we will search for in Spotify
    for query in search_list:
        payload = {
                'q':query, 
                'type':search_type, 
                'limit':limit
        } 
        #grab search result with exception handling
        search_response = requests.get(search_url, headers=headers, params=payload, timeout=10)
        #grab immediate errors thrown
        try:
            search_response.raise_for_status()
        except HTTPError as e:
            print(f"HTTP Error: {e}")
            continue
        except RequestException as e:
            print(f"Request failed: {e}")
            continue
        #Eror handling for JSON parsing
        try:
            data = search_response.json()
        except (ValueError, KeyError) as e:
            print(f"Failed to parse JSON for query '{query}': {e}")
            continue
        print(f"result for {query}")
        #Grab "items" within a search results for each result
        items = data.get(type_map[search_type], {}).get("items", [])
        print(f"Query: {query} -> {len(items)} results")
        #Append items to collected list
        all_results.extend(items)
    # Deduped search results
    unique_results = {p["id"]: p for p in all_results if p.get("id")}    
    print(f"Total results: {len(all_results)}")
    print(f"Unique results: {len(unique_results)}")
    print(list(unique_results.values()))
    #return deduped results
    return list(unique_results.values())


#Define main for reusability and importing
def main():
    genre_list = ["prog rock", "progressive rock", "math rock"]
    searches = spotify_searches(genre_list, "playlist", 2)
if __name__ == "__main__":
    main()