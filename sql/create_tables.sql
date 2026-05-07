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

CREATE TABLE fact_play_event (
    play_key SERIAL PRIMARY KEY,
    date_key INT REFERENCES dim_date(dim_date_key),
    track_key INT REFERENCES dim_track(track_key),
    artist_key INT REFERENCES dim_artist(artist_key),
    ms_played INT
);
CREATE TABLE IF NOT EXISTS public.llm_eval_log (
    eval_key SERIAL PRIMARY KEY,
    evaluated_at TIMESTAMP DEFAULT NOW(),
    question TEXT,
    generated_sql TEXT,
    passed BOOLEAN,
    score INT,
    reasoning TEXT,
    flags TEXT[]
);

CREATE TABLE IF NOT EXISTS public.discoveries (
    insight_key SERIAL PRIMARY KEY,
    generated_at TIMESTAMP DEFAULT NOW(),
    user_scope VARCHAR(50),
    insight_text TEXT,
    follow_up_question TEXT,
    used BOOLEAN DEFAULT FALSE,
    chart_spec JSONB,
    raw_data JSONB,
    generated_sql TEXT
);

CREATE TABLE IF NOT EXISTS public.discovery_eval_log(
    eval_key SERIAL PRIMARY KEY,
    evaluated_at TIMESTAMP DEFAULT NOW(),
    user_scope VARCHAR(50),
    insight_text TEXT,
    follow_up_question TEXT,
    passed BOOLEAN,
    score INT,
    reasoning TEXT,
    flags TEXT[]
);
