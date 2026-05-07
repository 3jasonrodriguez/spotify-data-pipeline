TOP_TEN_SONGS='''with plays as 
                    (SELECT artist_name, track_name, count(*) as play_counts
                    FROM {user}.fact_play_event f INNER JOIN {user}.dim_track t on f.track_key=t.track_key inner join {user}.dim_artist a on f.artist_key=a.artist_key
                    GROUP BY artist_name, track_name)
                SELECT artist_name, track_name, play_counts
                FROM plays
                ORDER BY play_counts DESC
                LIMIT 10'''

HOURS_PER_YEAR='''SELECT year, ROUND(SUM(ms_played) / 3600000.0, 1) as hours_played
                    FROM {user}.fact_play_event f INNER JOIN {user}.dim_date d on f.date_key=d.dim_date_key
                    GROUP BY year'''

GENRE_YEAR_TRENDS='''with year_genres as 
                    (SELECT year, genre_name, ROUND(SUM(ms_played) / 3600000.0, 1) as hours_played
                    FROM {user}.fact_play_event f INNER JOIN {user}.dim_artist a ON f.artist_key=a.artist_key INNER JOIN {user}.bridge_artist_genre b ON f.artist_key=b.artist_key INNER JOIN {user}.dim_genre g ON b.genre_key=g.genre_key INNER JOIN {user}.dim_date d ON f.date_key=d.dim_date_key
                    WHERE genre_name IS NOT NULL
                    GROUP BY year, genre_name), ranks as 
                    (SELECT year, genre_name, hours_played, row_number() over (partition by year order by hours_played desc) as rank
                    FROM year_genres)
                    SELECT year, genre_name, hours_played, rank
                    FROM ranks 
                    WHERE rank <=10
                    order by year, rank asc'''

DATE_STREAMS='''with day_plays as (SELECT full_date, artist_name, track_name, ROUND(SUM(ms_played) / 3600000.00, 2) as hours_played
                                        FROM {user}.dim_date d INNER JOIN {user}.fact_play_event f ON d.dim_date_key=f.date_key INNER JOIN {user}.dim_artist a ON f.artist_key=a.artist_key INNER JOIN {user}.dim_track t ON f.track_key=t.track_key
                                        GROUP BY full_date, artist_name, track_name)
                                        SELECT full_date, artist_name, track_name,hours_played
                                        FROM day_plays '''
ALL_ARTISTS='''SELECT artist_name
                FROM {user}.dim_artist a INNER JOIN {user}.fact_play_event f ON a.artist_key=f.artist_key
                WHERE artist_name IS NOT NULL'''
STREAMS_BY_DAY='''SELECT day_of_week, ROUND(SUM(ms_played) / 3600000.00, 2) as hours_played
                FROM {user}.dim_date d INNER JOIN {user}.fact_play_event f ON d.dim_date_key=f.date_key
                GROUP BY day_of_week'''

LISTENING_STREAK='''
WITH plays AS (
    SELECT DISTINCT track_name,artist_name, full_date
    FROM {user}.dim_track t 
    INNER JOIN {user}.fact_play_event f ON t.track_key = f.track_key 
    INNER JOIN {user}.dim_date d ON f.date_key = d.dim_date_key
    INNER JOIN {user}.dim_artist a ON f.artist_key = a.artist_key
),
counts AS (
    SELECT track_name, artist_name, full_date, 
        ROW_NUMBER() OVER (PARTITION BY track_name, artist_name ORDER BY full_date ASC) AS rn
    FROM plays
),
streak_groups AS (
    SELECT track_name, artist_name, full_date, rn, 
        full_date - CAST(rn AS INTEGER) AS day_diff
    FROM counts
),
streaks AS (
    SELECT track_name, artist_name, day_diff, COUNT(*) AS streak
    FROM streak_groups
    GROUP BY track_name, artist_name, day_diff
)
SELECT track_name, artist_name, MAX(streak) AS longest_streak_of_days
FROM streaks
GROUP BY track_name, artist_name
ORDER BY longest_streak_of_days DESC'''

LIBRARY_ADDS='''SELECT distinct artist_name, track_name, DATE(saved_at) as saved_at
            FROM {user}.dim_library l INNER JOIN {user}.dim_track t ON l.track_key=t.track_key
            INNER JOIN {user}.fact_play_event f ON t.track_key=f.track_key
            INNER JOIN {user}.dim_artist a ON f.artist_key=a.artist_key
'''

GET_USERS = """SELECT schema_name 
    FROM information_schema.schemata
    WHERE schema_name NOT IN ('information_schema', 'pg_catalog', 'public')
    AND schema_name NOT LIKE 'pg_toast%'
    AND schema_name NOT LIKE 'pg_temp%'
"""
KPIS='''SELECT
    COUNT(DISTINCT fpe.play_key) as total_streams,
    ROUND(SUM(fpe.ms_played) / 3600000.0, 1) as total_hours,
    COUNT(DISTINCT dd.full_date) as total_days,
    COUNT(DISTINCT dt.track_key) as total_tracks,
    COUNT(DISTINCT da.artist_key) as total_artists,
    COUNT(DISTINCT dg.genre_key) as total_genres
FROM {user}.fact_play_event fpe
JOIN {user}.dim_date dd ON fpe.date_key = dd.dim_date_key
JOIN {user}.dim_track dt ON fpe.track_key = dt.track_key
JOIN {user}.dim_artist da ON fpe.artist_key = da.artist_key
JOIN {user}.bridge_artist_genre bag ON da.artist_key = bag.artist_key
JOIN {user}.dim_genre dg ON bag.genre_key = dg.genre_key'''

GET_DISCOVERIES='''SELECT * FROM (
    SELECT *,
    ROW_NUMBER() OVER (PARTITION BY user_scope ORDER BY generated_at DESC) as rn
    FROM public.discoveries
) ranked
WHERE rn = 1'''
