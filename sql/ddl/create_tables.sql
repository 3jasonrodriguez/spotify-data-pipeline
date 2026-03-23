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

CREATE TABLE dim_track (
    track_key SERIAL PRIMARY KEY,
    spotify_track_id VARCHAR(30),
    track_name VARCHAR(255),
    duration_ms INT
);

CREATE TABLE dim_artist (
    artist_key SERIAL PRIMARY KEY,
    spotify_artist_id VARCHAR(30),
    artist_name VARCHAR(255)
);

CREATE TABLE dim_genre (
    genre_key SERIAL PRIMARY KEY,
    genre_name VARCHAR(255)
);

CREATE TABLE dim_library (
    library_key SERIAL PRIMARY KEY,
    track_key INT REFERENCES dim_track(track_key),
    saved_at TIMESTAMP
);

CREATE TABLE bridge_artist_genre (
    artist_key INT REFERENCES dim_artist(artist_key),
    genre_key INT REFERENCES dim_genre(genre_key),
    PRIMARY KEY (artist_key, genre_key)
);

CREATE TABLE fact_play_event (
    play_key SERIAL PRIMARY KEY,
    date_key INT REFERENCES dim_date(dim_date_key),
    track_key INT REFERENCES dim_track(track_key),
    artist_key INT REFERENCES dim_artist(artist_key),
    ms_played INT
);