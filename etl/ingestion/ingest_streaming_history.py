import yaml
import os
import json 
from datetime import datetime
from etl.ingestion.load_to_s3 import load_to_s3
from etl.utils.connections import get_spotify_credentials, get_aws_client
import logging
from etl.utils.logger import get_logger 
logger = get_logger(__name__)

def ingest_streaming_history():
    #Loading of config file with path to streaming history
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)
    #Loading the files from the paths
    path = config["paths"]["streaming_history"]
    #Only grab the audio files (json)
    json_files = [f for f in os.listdir(path) if f.endswith(".json")]
    #Using a dict to put each stream by year for later partitioning
    records_dict_year = {}
    #Fields removed from the spotify json records
    fields_to_remove = {'ip_addr', 'episode_name','episode_show_name','spotify_episode_uri', 'audiobook_title', 'audiobook_uri','audiobook_chapter_uri', 'audiobook_chapter_title'}
    #Loop through all files
    for filename in json_files:
        full_path = os.path.join(path, filename)
        with open(full_path, "r", encoding="utf-8") as f:
            records = json.load(f)
            for record in records:
                #Skip non audio streams
                if record.get('spotify_track_uri') is None:
                    continue
                filtered_record = {key: value for key, value in record.items() if key not in fields_to_remove}
                #Extract the year of the timestamp
                ts = filtered_record.get('ts')
                if not ts:
                    continue
                year = str(datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").year)
                #Place record into the year key
                if year in records_dict_year:
                    records_dict_year[year].append(filtered_record)
                else:
                    records_dict_year[year] = [filtered_record]
    return records_dict_year
            
def main():
    records_by_year = ingest_streaming_history()
if __name__ == "__main__":
    main()