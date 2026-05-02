JUDGE_CONTEXT = '''
## Database Schema for SQL Validation

### Users and Schemas
Each user has their own schema (e.g. jason, kelly). 
All table references must be prefixed with schema.table_name.

### Tables and Valid Columns

fact_play_event:
- play_key (SERIAL PK)
- date_key (FK -> dim_date.dim_date_key)
- track_key (FK -> dim_track.track_key)
- artist_key (FK -> dim_artist.artist_key)
- ms_played (INT)

dim_date:
- dim_date_key (SERIAL PK)
- full_date (DATE)
- is_work_hour (BOOL) -- defined as 8AM-5PM Eastern
- year (INT)
- month (INT)
- day (INT)
- hour (INT)
- day_of_week (VARCHAR)

dim_track:
- track_key (SERIAL PK)
- spotify_track_id (VARCHAR)
- track_name (VARCHAR)
- duration_ms (INT)

dim_artist:
- artist_key (SERIAL PK)
- spotify_artist_id (VARCHAR)
- artist_name (VARCHAR)

dim_genre:
- genre_key (SERIAL PK)
- genre_name (VARCHAR)

dim_library:
- library_key (SERIAL PK)
- track_key (FK -> dim_track.track_key)
- saved_at (TIMESTAMP)

bridge_artist_genre:
- artist_key (FK -> dim_artist.artist_key)
- genre_key (FK -> dim_genre.genre_key)
- PRIMARY KEY (artist_key, genre_key)

### Key Relationships
- fact_play_event joins to dim_date, dim_track, dim_artist via foreign keys
- artist to genre is many-to-many via bridge_artist_genre
- dim_library tracks saved songs, not all saved songs appear in fact_play_event
- Cross schema joins must use human readable fields not serial keys

### Common Pitfalls to Flag
- Wrong column names (e.g. genre_id instead of genre_key)
- Missing schema prefix on table references
- Joining dim_library directly to fact_play_event without going through dim_track
- Using play_key as a measure instead of COUNT(play_key)
- Missing GROUP BY when using aggregates
'''