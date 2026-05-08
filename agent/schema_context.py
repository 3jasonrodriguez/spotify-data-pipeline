SCHEMA_CONTEXT='''
##Overview of Data Sources:
This spotify postgres db has data from user's streaming history downloaded from spotify, generated from json files. 
These files hold every play event (music only) for a user's profile. Additionally there is data from the user's library (saved tracks). 
These are the two main sources of data. There are records that may be in the streaming history but not in the library for awareness. 

##Fact Table:
The fact table has a dim date key, artist key, track key, a play key (for every play event) and ms played for how long the stream was. 
Each column (aside from play key and ms played) are foreign keys from the corresponding dim_* table's primary key. 


##Artists and Genres Relationship:
The relationship between artists and genres is one to many, although not every artist has genres tagged due to the source being not so clean all the time. 
There is a bridge artist genre table of foreign keys with a composite key of those FKs.
To grab genres, you will need to go through the bridge artist genre table with an artist key to map to a genre key.
Artists are derived from the saved tracks, not streaming history. 


There is a unique key on each table for the corresponding key.

##Schemas references for users:
The database contains schemas per user, so table references will need to contain schema.table_name for the right user.
The users could grow - if needed you can check the metadata in postgres to grab the users. They should be lower case first names for valid users.
Here's the query to validate users:
SELECT schema_name FROM information_schema.schemata 
WHERE schema_name NOT IN ('information_schema', 'pg_catalog', 'public')
AND schema_name NOT LIKE 'pg_%'
Personal questions asked for only one user scope should NEVER use cross-schema queries.
Always query only the specified user's schema for personal questions.

## Library and Artist joins
dim_library has no direct relationship to dim_artist.
To find artist information for library tracks, join:
dim_library → dim_track (via track_key) → fact_play_event (via track_key) → dim_artist (via artist_key)
Use DISTINCT or GROUP BY to avoid duplicates from multiple play events.
If a track has never been played it will not appear in fact_play_event.
For library queries that need artist info regardless of play history,
use a LEFT JOIN to fact_play_event and handle NULLs accordingly.

##Cross schema queries and joins:
Cross schema queries are valid since the schemas are in the same database and the tables can be cross joined.
Since the keys will be different, cross joins will need to be by human readable data (e.g. track name, artist name, etc.) instead of serial keys.
This will be when analysis is required for comparisions or contrasts between users/schemas.
Only use cross-schema UNION ALL queries when the user explicitly asks to "compare" both users or asks about "both users" or "everyone" or all users - meaning the user scope is "compare".
If the user scope is set to compare, then data from both schemas will need to be explored and the resulting data should contain data from both user schemas.


## Cross-schema query patterns
When querying across schemas, always:
- UNION results from each schema with a 'user_name' column added to identify the source
- Example pattern:
  SELECT 'jason' as user_name, artist_name, COUNT(*) as play_count 
  FROM jason.fact_play_event fpe
  JOIN jason.dim_artist da ON fpe.artist_key = da.artist_key
  GROUP BY artist_name
  UNION ALL
  SELECT 'kelly' as user_name, artist_name, COUNT(*) as play_count
  FROM kelly.fact_play_event fpe  
  JOIN kelly.dim_artist da ON fpe.artist_key = da.artist_key
  GROUP BY artist_name

Example analytical questions:
Top 10 most time-listened tracks of all time
Listening history over time by genre
Top 10 tracks played during work hours
Total listening time per year
Saved library tracks never played
Longest consecutive listening streak by track

##DDL for tables in a schema (per user):
#is_work_hour is originally defined as between 8AM-5PM Eastern time (America/New York)
CREATE TABLE dim_date (
    dim_date_key SERIAL PRIMARY KEY,
    full_date DATE,
    is_work_hour BOOL,
    year INT,
    month INT,
    day INT,
    hour INT,
    day_of_week VARCHAR(10)
);

ALTER TABLE dim_date ADD CONSTRAINT unique_date_hour UNIQUE (full_date, hour);

#duration_ms is measuring the milliseconds for a track's length
CREATE TABLE dim_track (
    track_key SERIAL PRIMARY KEY,
    spotify_track_id VARCHAR(30),
    track_name VARCHAR(255),
    duration_ms INT
);
ALTER TABLE dim_track ADD CONSTRAINT unique_spotify_track_id UNIQUE (spotify_track_id);


CREATE TABLE dim_artist (
    artist_key SERIAL PRIMARY KEY,
    spotify_artist_id VARCHAR(30),
    artist_name VARCHAR(255)
);
ALTER TABLE dim_artist ADD CONSTRAINT unique_spotify_artist_id UNIQUE (spotify_artist_id);
ALTER TABLE dim_artist ADD CONSTRAINT unique_artist_name UNIQUE (artist_name);

CREATE TABLE dim_genre (
    genre_key SERIAL PRIMARY KEY,
    genre_name VARCHAR(255)
);
ALTER TABLE dim_genre ADD CONSTRAINT unique_genre_name UNIQUE (genre_name);

#saved_at is the timestamp for when a track was added to my library
CREATE TABLE dim_library (
    library_key SERIAL PRIMARY KEY,
    track_key INT REFERENCES dim_track(track_key),
    saved_at TIMESTAMP
);
ALTER TABLE dim_library ADD CONSTRAINT unique_library_track UNIQUE (track_key);

CREATE TABLE bridge_artist_genre (
    artist_key INT REFERENCES dim_artist(artist_key),
    genre_key INT REFERENCES dim_genre(genre_key),
    PRIMARY KEY (artist_key, genre_key)
);

#ms_played is how long in milliseconds a track was played
CREATE TABLE fact_play_event (
    play_key SERIAL PRIMARY KEY,
    date_key INT REFERENCES dim_date(dim_date_key),
    track_key INT REFERENCES dim_track(track_key),
    artist_key INT REFERENCES dim_artist(artist_key),
    ms_played INT
);
'''