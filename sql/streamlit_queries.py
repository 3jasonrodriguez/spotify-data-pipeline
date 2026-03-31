TOP_TEN_SONGS='''with plays as 
                    (SELECT artist_name, track_name, count(*) as play_counts
                    FROM fact_play_event f INNER JOIN dim_track t on f.track_key=t.track_key inner join dim_artist a on f.artist_key=a.artist_key
                    GROUP BY artist_name, track_name)
                SELECT artist_name, track_name, play_counts
                FROM plays
                ORDER BY play_counts DESC
                LIMIT 10'''

HOURS_PER_YEAR='''SELECT year, ROUND(SUM(ms_played) / 3600000.0, 1) as hours_played
                    FROM fact_play_event f INNER JOIN dim_date d on f.date_key=d.dim_date_key
                    GROUP BY year'''

GENRE_YEAR_TRENDS='''with year_genres as 
                    (SELECT year, genre_name, ROUND(SUM(ms_played) / 3600000.0, 1) as hours_played
                    FROM fact_play_event f INNER JOIN dim_artist a ON f.artist_key=a.artist_key INNER JOIN bridge_artist_genre b ON f.artist_key=b.artist_key INNER JOIN dim_genre g ON b.genre_key=g.genre_key INNER JOIN dim_date d ON f.date_key=d.dim_date_key
                    WHERE genre_name IS NOT NULL
                    GROUP BY year, genre_name), ranks as 
                    (SELECT year, genre_name, hours_played, row_number() over (partition by year order by hours_played desc) as rank
                    FROM year_genres)
                    SELECT year, genre_name, hours_played, rank
                    FROM ranks 
                    WHERE rank <=3
                    order by year, rank asc'''

DATE_STREAMS='''with day_plays as (SELECT full_date, artist_name, track_name, ROUND(SUM(ms_played) / 3600000.00, 2) as hours_played
                                        FROM dim_date d INNER JOIN fact_play_event f ON d.dim_date_key=f.date_key INNER JOIN dim_artist a ON f.artist_key=a.artist_key INNER JOIN dim_track t ON f.track_key=t.track_key
                                        GROUP BY full_date, artist_name, track_name)
                                        SELECT full_date, artist_name, track_name,hours_played
                                        FROM day_plays '''