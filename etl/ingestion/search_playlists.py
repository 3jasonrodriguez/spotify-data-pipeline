from etl.utils.spotify_auth import get_spotify_access_token
import requests
from requests.exceptions import RequestException, HTTPError
from etl.utils.logger import get_logger 
logger = get_logger(__name__)
#Function to iterate over a list of searchable objects in the Spotify search.
#Search_list is a list of the strings for the object type we will search through
#Search types are defined within this function in a map
#Limit is defined for returning results. The max is 50 in the API.
def spotify_searches(search_list, search_type, limit, user="jason"):
    #Used for the "object" type in Spotify that we are searching for. The plural form is used within the nested JSON
    type_map = {"playlist":"playlists", "artist":"artists", "track":"tracks", "album":"albums"}
    if search_type not in type_map:
        raise ValueError(f"Invalid search type: {search_type}")
    #list to collect all search results
    all_results = []

    #Build out search API call
    token = get_spotify_access_token(user)
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

        #grab immediate errors thrown
        try:
            #grab search result with exception handling
            search_response = requests.get(search_url, headers=headers, params=payload, timeout=10)
            search_response.raise_for_status()
            data = search_response.json()

        except HTTPError as e:
            logger.error(f"HTTP Error: {e}")
            continue
        except RequestException as e:
            logger.error(f"Request failed: {e}")
            continue
        #JSON parsing errors
        except (ValueError, KeyError) as e:
            logger.error(f"Failed to parse JSON for query '{query}': {e}")
            continue

        logger.debug(f"result for {query}")
        #Grab items within a search result, even if the search types and items keys are missing
        items = data.get(type_map[search_type], {}).get("items", [])
        #strip the quotes before looking for names and descriptions
        clean_query = query.lower()
        #Looks for matches containing the query (Spotify is looking for the query string in the name and description)
        cleansed_items = [
            p for p in items
            if p and (
                clean_query in p.get("name", "").lower() or
                clean_query in p.get("description", "").lower()
            )
        ]        
        logger.debug(f"Query: {query} -> {len(cleansed_items)} results")
        #Append items to collected list
        all_results.extend(cleansed_items)
    # Deduped search results by creating a dictionary keyed by id.
    unique_results = {result["id"]: result for result in all_results if result and result.get("id")}
    logger.info(f"Total results: {len(all_results)}")
    logger.info(f"Unique results: {len(unique_results)}")
    #return deduped results
    return list(unique_results.values())


#Define main for reusability and importing
def main():
    genre_list = ["prog rock", "progressive rock", "math rock"]
    user = input("Please enter user:" )
    searches = spotify_searches(genre_list, "playlists", 10, user)
if __name__ == "__main__":
    main()