import yaml
import os
import json 
from datetime import datetime
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

path = config["paths"]["streaming_history"]
files = os.listdir(path)
json_files = [f for f in os.listdir(path) if f.endswith(".json")]

for filename in json_files:
    full_path = os.path.join(path, filename)
    with open(full_path, "r", encoding="utf-8") as f:
        records = json.load(f)
for record in records:
    year = datetime.strptime(record.get('ts'), "%Y-%m-%dT%H:%M:%SZ").year
    print(year)