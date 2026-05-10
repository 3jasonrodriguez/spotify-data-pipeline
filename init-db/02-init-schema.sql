--
-- PostgreSQL database dump
--

\restrict 20MVmvrtsUgIlLqftqCmBdvlhv2P3kfJcDn4ZkYAlK9gnqEDncuhfc6nxUelrJz

-- Dumped from database version 16.13 (Debian 16.13-1.pgdg13+1)
-- Dumped by pg_dump version 16.13 (Debian 16.13-1.pgdg13+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: jason; Type: SCHEMA; Schema: -; Owner: airflow
--

CREATE SCHEMA jason;


ALTER SCHEMA jason OWNER TO airflow;

--
-- Name: kelly; Type: SCHEMA; Schema: -; Owner: airflow
--

CREATE SCHEMA kelly;


ALTER SCHEMA kelly OWNER TO airflow;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: bridge_artist_genre; Type: TABLE; Schema: jason; Owner: airflow
--

CREATE TABLE jason.bridge_artist_genre (
    artist_key integer NOT NULL,
    genre_key integer NOT NULL
);


ALTER TABLE jason.bridge_artist_genre OWNER TO airflow;

--
-- Name: dim_artist; Type: TABLE; Schema: jason; Owner: airflow
--

CREATE TABLE jason.dim_artist (
    artist_key integer NOT NULL,
    spotify_artist_id character varying(30),
    artist_name character varying(255)
);


ALTER TABLE jason.dim_artist OWNER TO airflow;

--
-- Name: dim_artist_artist_key_seq; Type: SEQUENCE; Schema: jason; Owner: airflow
--

CREATE SEQUENCE jason.dim_artist_artist_key_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE jason.dim_artist_artist_key_seq OWNER TO airflow;

--
-- Name: dim_artist_artist_key_seq; Type: SEQUENCE OWNED BY; Schema: jason; Owner: airflow
--

ALTER SEQUENCE jason.dim_artist_artist_key_seq OWNED BY jason.dim_artist.artist_key;


--
-- Name: dim_date; Type: TABLE; Schema: jason; Owner: airflow
--

CREATE TABLE jason.dim_date (
    dim_date_key integer NOT NULL,
    full_date date,
    is_work_hour boolean,
    year integer,
    month integer,
    day integer,
    hour integer,
    day_of_week character varying(10)
);


ALTER TABLE jason.dim_date OWNER TO airflow;

--
-- Name: dim_date_dim_date_key_seq; Type: SEQUENCE; Schema: jason; Owner: airflow
--

CREATE SEQUENCE jason.dim_date_dim_date_key_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE jason.dim_date_dim_date_key_seq OWNER TO airflow;

--
-- Name: dim_date_dim_date_key_seq; Type: SEQUENCE OWNED BY; Schema: jason; Owner: airflow
--

ALTER SEQUENCE jason.dim_date_dim_date_key_seq OWNED BY jason.dim_date.dim_date_key;


--
-- Name: dim_genre; Type: TABLE; Schema: jason; Owner: airflow
--

CREATE TABLE jason.dim_genre (
    genre_key integer NOT NULL,
    genre_name character varying(255)
);


ALTER TABLE jason.dim_genre OWNER TO airflow;

--
-- Name: dim_genre_genre_key_seq; Type: SEQUENCE; Schema: jason; Owner: airflow
--

CREATE SEQUENCE jason.dim_genre_genre_key_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE jason.dim_genre_genre_key_seq OWNER TO airflow;

--
-- Name: dim_genre_genre_key_seq; Type: SEQUENCE OWNED BY; Schema: jason; Owner: airflow
--

ALTER SEQUENCE jason.dim_genre_genre_key_seq OWNED BY jason.dim_genre.genre_key;


--
-- Name: dim_library; Type: TABLE; Schema: jason; Owner: airflow
--

CREATE TABLE jason.dim_library (
    library_key integer NOT NULL,
    track_key integer,
    saved_at timestamp without time zone
);


ALTER TABLE jason.dim_library OWNER TO airflow;

--
-- Name: dim_library_library_key_seq; Type: SEQUENCE; Schema: jason; Owner: airflow
--

CREATE SEQUENCE jason.dim_library_library_key_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE jason.dim_library_library_key_seq OWNER TO airflow;

--
-- Name: dim_library_library_key_seq; Type: SEQUENCE OWNED BY; Schema: jason; Owner: airflow
--

ALTER SEQUENCE jason.dim_library_library_key_seq OWNED BY jason.dim_library.library_key;


--
-- Name: dim_track; Type: TABLE; Schema: jason; Owner: airflow
--

CREATE TABLE jason.dim_track (
    track_key integer NOT NULL,
    spotify_track_id character varying(30),
    track_name character varying(255),
    duration_ms integer
);


ALTER TABLE jason.dim_track OWNER TO airflow;

--
-- Name: dim_track_track_key_seq; Type: SEQUENCE; Schema: jason; Owner: airflow
--

CREATE SEQUENCE jason.dim_track_track_key_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE jason.dim_track_track_key_seq OWNER TO airflow;

--
-- Name: dim_track_track_key_seq; Type: SEQUENCE OWNED BY; Schema: jason; Owner: airflow
--

ALTER SEQUENCE jason.dim_track_track_key_seq OWNED BY jason.dim_track.track_key;


--
-- Name: fact_play_event; Type: TABLE; Schema: jason; Owner: airflow
--

CREATE TABLE jason.fact_play_event (
    play_key integer NOT NULL,
    date_key integer,
    track_key integer,
    artist_key integer,
    ms_played integer
);


ALTER TABLE jason.fact_play_event OWNER TO airflow;

--
-- Name: fact_play_event_play_key_seq; Type: SEQUENCE; Schema: jason; Owner: airflow
--

CREATE SEQUENCE jason.fact_play_event_play_key_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE jason.fact_play_event_play_key_seq OWNER TO airflow;

--
-- Name: fact_play_event_play_key_seq; Type: SEQUENCE OWNED BY; Schema: jason; Owner: airflow
--

ALTER SEQUENCE jason.fact_play_event_play_key_seq OWNED BY jason.fact_play_event.play_key;


--
-- Name: bridge_artist_genre; Type: TABLE; Schema: kelly; Owner: airflow
--

CREATE TABLE kelly.bridge_artist_genre (
    artist_key integer NOT NULL,
    genre_key integer NOT NULL
);


ALTER TABLE kelly.bridge_artist_genre OWNER TO airflow;

--
-- Name: dim_artist; Type: TABLE; Schema: kelly; Owner: airflow
--

CREATE TABLE kelly.dim_artist (
    artist_key integer NOT NULL,
    spotify_artist_id character varying(30),
    artist_name character varying(255)
);


ALTER TABLE kelly.dim_artist OWNER TO airflow;

--
-- Name: dim_artist_artist_key_seq; Type: SEQUENCE; Schema: kelly; Owner: airflow
--

CREATE SEQUENCE kelly.dim_artist_artist_key_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE kelly.dim_artist_artist_key_seq OWNER TO airflow;

--
-- Name: dim_artist_artist_key_seq; Type: SEQUENCE OWNED BY; Schema: kelly; Owner: airflow
--

ALTER SEQUENCE kelly.dim_artist_artist_key_seq OWNED BY kelly.dim_artist.artist_key;


--
-- Name: dim_date; Type: TABLE; Schema: kelly; Owner: airflow
--

CREATE TABLE kelly.dim_date (
    dim_date_key integer NOT NULL,
    full_date date,
    is_work_hour boolean,
    year integer,
    month integer,
    day integer,
    hour integer,
    day_of_week character varying(10)
);


ALTER TABLE kelly.dim_date OWNER TO airflow;

--
-- Name: dim_date_dim_date_key_seq; Type: SEQUENCE; Schema: kelly; Owner: airflow
--

CREATE SEQUENCE kelly.dim_date_dim_date_key_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE kelly.dim_date_dim_date_key_seq OWNER TO airflow;

--
-- Name: dim_date_dim_date_key_seq; Type: SEQUENCE OWNED BY; Schema: kelly; Owner: airflow
--

ALTER SEQUENCE kelly.dim_date_dim_date_key_seq OWNED BY kelly.dim_date.dim_date_key;


--
-- Name: dim_genre; Type: TABLE; Schema: kelly; Owner: airflow
--

CREATE TABLE kelly.dim_genre (
    genre_key integer NOT NULL,
    genre_name character varying(255)
);


ALTER TABLE kelly.dim_genre OWNER TO airflow;

--
-- Name: dim_genre_genre_key_seq; Type: SEQUENCE; Schema: kelly; Owner: airflow
--

CREATE SEQUENCE kelly.dim_genre_genre_key_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE kelly.dim_genre_genre_key_seq OWNER TO airflow;

--
-- Name: dim_genre_genre_key_seq; Type: SEQUENCE OWNED BY; Schema: kelly; Owner: airflow
--

ALTER SEQUENCE kelly.dim_genre_genre_key_seq OWNED BY kelly.dim_genre.genre_key;


--
-- Name: dim_library; Type: TABLE; Schema: kelly; Owner: airflow
--

CREATE TABLE kelly.dim_library (
    library_key integer NOT NULL,
    track_key integer,
    saved_at timestamp without time zone
);


ALTER TABLE kelly.dim_library OWNER TO airflow;

--
-- Name: dim_library_library_key_seq; Type: SEQUENCE; Schema: kelly; Owner: airflow
--

CREATE SEQUENCE kelly.dim_library_library_key_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE kelly.dim_library_library_key_seq OWNER TO airflow;

--
-- Name: dim_library_library_key_seq; Type: SEQUENCE OWNED BY; Schema: kelly; Owner: airflow
--

ALTER SEQUENCE kelly.dim_library_library_key_seq OWNED BY kelly.dim_library.library_key;


--
-- Name: dim_track; Type: TABLE; Schema: kelly; Owner: airflow
--

CREATE TABLE kelly.dim_track (
    track_key integer NOT NULL,
    spotify_track_id character varying(30),
    track_name character varying(255),
    duration_ms integer
);


ALTER TABLE kelly.dim_track OWNER TO airflow;

--
-- Name: dim_track_track_key_seq; Type: SEQUENCE; Schema: kelly; Owner: airflow
--

CREATE SEQUENCE kelly.dim_track_track_key_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE kelly.dim_track_track_key_seq OWNER TO airflow;

--
-- Name: dim_track_track_key_seq; Type: SEQUENCE OWNED BY; Schema: kelly; Owner: airflow
--

ALTER SEQUENCE kelly.dim_track_track_key_seq OWNED BY kelly.dim_track.track_key;


--
-- Name: fact_play_event; Type: TABLE; Schema: kelly; Owner: airflow
--

CREATE TABLE kelly.fact_play_event (
    play_key integer NOT NULL,
    date_key integer,
    track_key integer,
    artist_key integer,
    ms_played integer
);


ALTER TABLE kelly.fact_play_event OWNER TO airflow;

--
-- Name: fact_play_event_play_key_seq; Type: SEQUENCE; Schema: kelly; Owner: airflow
--

CREATE SEQUENCE kelly.fact_play_event_play_key_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE kelly.fact_play_event_play_key_seq OWNER TO airflow;

--
-- Name: fact_play_event_play_key_seq; Type: SEQUENCE OWNED BY; Schema: kelly; Owner: airflow
--

ALTER SEQUENCE kelly.fact_play_event_play_key_seq OWNED BY kelly.fact_play_event.play_key;


--
-- Name: discoveries; Type: TABLE; Schema: public; Owner: airflow
--

CREATE TABLE public.discoveries (
    insight_key integer NOT NULL,
    generated_at timestamp without time zone DEFAULT now(),
    user_scope character varying(50),
    insight_text text,
    follow_up_question text,
    used boolean DEFAULT false,
    chart_spec jsonb,
    raw_data jsonb,
    generated_sql text
);


ALTER TABLE public.discoveries OWNER TO airflow;

--
-- Name: discoveries_insight_key_seq; Type: SEQUENCE; Schema: public; Owner: airflow
--

CREATE SEQUENCE public.discoveries_insight_key_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.discoveries_insight_key_seq OWNER TO airflow;

--
-- Name: discoveries_insight_key_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: airflow
--

ALTER SEQUENCE public.discoveries_insight_key_seq OWNED BY public.discoveries.insight_key;


--
-- Name: discovery_eval_log; Type: TABLE; Schema: public; Owner: airflow
--

CREATE TABLE public.discovery_eval_log (
    eval_key integer NOT NULL,
    evaluated_at timestamp without time zone DEFAULT now(),
    user_scope character varying(50),
    insight_text text,
    follow_up_question text,
    passed boolean,
    score integer,
    reasoning text,
    flags text[]
);


ALTER TABLE public.discovery_eval_log OWNER TO airflow;

--
-- Name: discovery_eval_log_eval_key_seq; Type: SEQUENCE; Schema: public; Owner: airflow
--

CREATE SEQUENCE public.discovery_eval_log_eval_key_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.discovery_eval_log_eval_key_seq OWNER TO airflow;

--
-- Name: discovery_eval_log_eval_key_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: airflow
--

ALTER SEQUENCE public.discovery_eval_log_eval_key_seq OWNED BY public.discovery_eval_log.eval_key;


--
-- Name: llm_eval_log; Type: TABLE; Schema: public; Owner: airflow
--

CREATE TABLE public.llm_eval_log (
    eval_key integer NOT NULL,
    evaluated_at timestamp without time zone DEFAULT now(),
    question text,
    generated_sql text,
    passed boolean,
    score integer,
    reasoning text,
    flags text[],
    user_scope character varying(50)
);


ALTER TABLE public.llm_eval_log OWNER TO airflow;

--
-- Name: llm_eval_log_eval_key_seq; Type: SEQUENCE; Schema: public; Owner: airflow
--

CREATE SEQUENCE public.llm_eval_log_eval_key_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.llm_eval_log_eval_key_seq OWNER TO airflow;

--
-- Name: llm_eval_log_eval_key_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: airflow
--

ALTER SEQUENCE public.llm_eval_log_eval_key_seq OWNED BY public.llm_eval_log.eval_key;


--
-- Name: dim_artist artist_key; Type: DEFAULT; Schema: jason; Owner: airflow
--

ALTER TABLE ONLY jason.dim_artist ALTER COLUMN artist_key SET DEFAULT nextval('jason.dim_artist_artist_key_seq'::regclass);


--
-- Name: dim_date dim_date_key; Type: DEFAULT; Schema: jason; Owner: airflow
--

ALTER TABLE ONLY jason.dim_date ALTER COLUMN dim_date_key SET DEFAULT nextval('jason.dim_date_dim_date_key_seq'::regclass);


--
-- Name: dim_genre genre_key; Type: DEFAULT; Schema: jason; Owner: airflow
--

ALTER TABLE ONLY jason.dim_genre ALTER COLUMN genre_key SET DEFAULT nextval('jason.dim_genre_genre_key_seq'::regclass);


--
-- Name: dim_library library_key; Type: DEFAULT; Schema: jason; Owner: airflow
--

ALTER TABLE ONLY jason.dim_library ALTER COLUMN library_key SET DEFAULT nextval('jason.dim_library_library_key_seq'::regclass);


--
-- Name: dim_track track_key; Type: DEFAULT; Schema: jason; Owner: airflow
--

ALTER TABLE ONLY jason.dim_track ALTER COLUMN track_key SET DEFAULT nextval('jason.dim_track_track_key_seq'::regclass);


--
-- Name: fact_play_event play_key; Type: DEFAULT; Schema: jason; Owner: airflow
--

ALTER TABLE ONLY jason.fact_play_event ALTER COLUMN play_key SET DEFAULT nextval('jason.fact_play_event_play_key_seq'::regclass);


--
-- Name: dim_artist artist_key; Type: DEFAULT; Schema: kelly; Owner: airflow
--

ALTER TABLE ONLY kelly.dim_artist ALTER COLUMN artist_key SET DEFAULT nextval('kelly.dim_artist_artist_key_seq'::regclass);


--
-- Name: dim_date dim_date_key; Type: DEFAULT; Schema: kelly; Owner: airflow
--

ALTER TABLE ONLY kelly.dim_date ALTER COLUMN dim_date_key SET DEFAULT nextval('kelly.dim_date_dim_date_key_seq'::regclass);


--
-- Name: dim_genre genre_key; Type: DEFAULT; Schema: kelly; Owner: airflow
--

ALTER TABLE ONLY kelly.dim_genre ALTER COLUMN genre_key SET DEFAULT nextval('kelly.dim_genre_genre_key_seq'::regclass);


--
-- Name: dim_library library_key; Type: DEFAULT; Schema: kelly; Owner: airflow
--

ALTER TABLE ONLY kelly.dim_library ALTER COLUMN library_key SET DEFAULT nextval('kelly.dim_library_library_key_seq'::regclass);


--
-- Name: dim_track track_key; Type: DEFAULT; Schema: kelly; Owner: airflow
--

ALTER TABLE ONLY kelly.dim_track ALTER COLUMN track_key SET DEFAULT nextval('kelly.dim_track_track_key_seq'::regclass);


--
-- Name: fact_play_event play_key; Type: DEFAULT; Schema: kelly; Owner: airflow
--

ALTER TABLE ONLY kelly.fact_play_event ALTER COLUMN play_key SET DEFAULT nextval('kelly.fact_play_event_play_key_seq'::regclass);


--
-- Name: discoveries insight_key; Type: DEFAULT; Schema: public; Owner: airflow
--

ALTER TABLE ONLY public.discoveries ALTER COLUMN insight_key SET DEFAULT nextval('public.discoveries_insight_key_seq'::regclass);


--
-- Name: discovery_eval_log eval_key; Type: DEFAULT; Schema: public; Owner: airflow
--

ALTER TABLE ONLY public.discovery_eval_log ALTER COLUMN eval_key SET DEFAULT nextval('public.discovery_eval_log_eval_key_seq'::regclass);


--
-- Name: llm_eval_log eval_key; Type: DEFAULT; Schema: public; Owner: airflow
--

ALTER TABLE ONLY public.llm_eval_log ALTER COLUMN eval_key SET DEFAULT nextval('public.llm_eval_log_eval_key_seq'::regclass);


--
-- Name: bridge_artist_genre bridge_artist_genre_pkey; Type: CONSTRAINT; Schema: jason; Owner: airflow
--

ALTER TABLE ONLY jason.bridge_artist_genre
    ADD CONSTRAINT bridge_artist_genre_pkey PRIMARY KEY (artist_key, genre_key);


--
-- Name: dim_artist dim_artist_pkey; Type: CONSTRAINT; Schema: jason; Owner: airflow
--

ALTER TABLE ONLY jason.dim_artist
    ADD CONSTRAINT dim_artist_pkey PRIMARY KEY (artist_key);


--
-- Name: dim_date dim_date_pkey; Type: CONSTRAINT; Schema: jason; Owner: airflow
--

ALTER TABLE ONLY jason.dim_date
    ADD CONSTRAINT dim_date_pkey PRIMARY KEY (dim_date_key);


--
-- Name: dim_genre dim_genre_pkey; Type: CONSTRAINT; Schema: jason; Owner: airflow
--

ALTER TABLE ONLY jason.dim_genre
    ADD CONSTRAINT dim_genre_pkey PRIMARY KEY (genre_key);


--
-- Name: dim_library dim_library_pkey; Type: CONSTRAINT; Schema: jason; Owner: airflow
--

ALTER TABLE ONLY jason.dim_library
    ADD CONSTRAINT dim_library_pkey PRIMARY KEY (library_key);


--
-- Name: dim_track dim_track_pkey; Type: CONSTRAINT; Schema: jason; Owner: airflow
--

ALTER TABLE ONLY jason.dim_track
    ADD CONSTRAINT dim_track_pkey PRIMARY KEY (track_key);


--
-- Name: fact_play_event fact_play_event_pkey; Type: CONSTRAINT; Schema: jason; Owner: airflow
--

ALTER TABLE ONLY jason.fact_play_event
    ADD CONSTRAINT fact_play_event_pkey PRIMARY KEY (play_key);


--
-- Name: dim_artist unique_artist_name; Type: CONSTRAINT; Schema: jason; Owner: airflow
--

ALTER TABLE ONLY jason.dim_artist
    ADD CONSTRAINT unique_artist_name UNIQUE (artist_name);


--
-- Name: dim_date unique_date_hour; Type: CONSTRAINT; Schema: jason; Owner: airflow
--

ALTER TABLE ONLY jason.dim_date
    ADD CONSTRAINT unique_date_hour UNIQUE (full_date, hour);


--
-- Name: dim_genre unique_genre_name; Type: CONSTRAINT; Schema: jason; Owner: airflow
--

ALTER TABLE ONLY jason.dim_genre
    ADD CONSTRAINT unique_genre_name UNIQUE (genre_name);


--
-- Name: dim_library unique_library_track; Type: CONSTRAINT; Schema: jason; Owner: airflow
--

ALTER TABLE ONLY jason.dim_library
    ADD CONSTRAINT unique_library_track UNIQUE (track_key);


--
-- Name: dim_artist unique_spotify_artist_id; Type: CONSTRAINT; Schema: jason; Owner: airflow
--

ALTER TABLE ONLY jason.dim_artist
    ADD CONSTRAINT unique_spotify_artist_id UNIQUE (spotify_artist_id);


--
-- Name: dim_track unique_spotify_track_id; Type: CONSTRAINT; Schema: jason; Owner: airflow
--

ALTER TABLE ONLY jason.dim_track
    ADD CONSTRAINT unique_spotify_track_id UNIQUE (spotify_track_id);


--
-- Name: bridge_artist_genre bridge_artist_genre_pkey; Type: CONSTRAINT; Schema: kelly; Owner: airflow
--

ALTER TABLE ONLY kelly.bridge_artist_genre
    ADD CONSTRAINT bridge_artist_genre_pkey PRIMARY KEY (artist_key, genre_key);


--
-- Name: dim_artist dim_artist_pkey; Type: CONSTRAINT; Schema: kelly; Owner: airflow
--

ALTER TABLE ONLY kelly.dim_artist
    ADD CONSTRAINT dim_artist_pkey PRIMARY KEY (artist_key);


--
-- Name: dim_date dim_date_pkey; Type: CONSTRAINT; Schema: kelly; Owner: airflow
--

ALTER TABLE ONLY kelly.dim_date
    ADD CONSTRAINT dim_date_pkey PRIMARY KEY (dim_date_key);


--
-- Name: dim_genre dim_genre_pkey; Type: CONSTRAINT; Schema: kelly; Owner: airflow
--

ALTER TABLE ONLY kelly.dim_genre
    ADD CONSTRAINT dim_genre_pkey PRIMARY KEY (genre_key);


--
-- Name: dim_library dim_library_pkey; Type: CONSTRAINT; Schema: kelly; Owner: airflow
--

ALTER TABLE ONLY kelly.dim_library
    ADD CONSTRAINT dim_library_pkey PRIMARY KEY (library_key);


--
-- Name: dim_track dim_track_pkey; Type: CONSTRAINT; Schema: kelly; Owner: airflow
--

ALTER TABLE ONLY kelly.dim_track
    ADD CONSTRAINT dim_track_pkey PRIMARY KEY (track_key);


--
-- Name: fact_play_event fact_play_event_pkey; Type: CONSTRAINT; Schema: kelly; Owner: airflow
--

ALTER TABLE ONLY kelly.fact_play_event
    ADD CONSTRAINT fact_play_event_pkey PRIMARY KEY (play_key);


--
-- Name: dim_artist unique_artist_name; Type: CONSTRAINT; Schema: kelly; Owner: airflow
--

ALTER TABLE ONLY kelly.dim_artist
    ADD CONSTRAINT unique_artist_name UNIQUE (artist_name);


--
-- Name: dim_date unique_date_hour; Type: CONSTRAINT; Schema: kelly; Owner: airflow
--

ALTER TABLE ONLY kelly.dim_date
    ADD CONSTRAINT unique_date_hour UNIQUE (full_date, hour);


--
-- Name: dim_genre unique_genre_name; Type: CONSTRAINT; Schema: kelly; Owner: airflow
--

ALTER TABLE ONLY kelly.dim_genre
    ADD CONSTRAINT unique_genre_name UNIQUE (genre_name);


--
-- Name: dim_library unique_library_track; Type: CONSTRAINT; Schema: kelly; Owner: airflow
--

ALTER TABLE ONLY kelly.dim_library
    ADD CONSTRAINT unique_library_track UNIQUE (track_key);


--
-- Name: dim_artist unique_spotify_artist_id; Type: CONSTRAINT; Schema: kelly; Owner: airflow
--

ALTER TABLE ONLY kelly.dim_artist
    ADD CONSTRAINT unique_spotify_artist_id UNIQUE (spotify_artist_id);


--
-- Name: dim_track unique_spotify_track_id; Type: CONSTRAINT; Schema: kelly; Owner: airflow
--

ALTER TABLE ONLY kelly.dim_track
    ADD CONSTRAINT unique_spotify_track_id UNIQUE (spotify_track_id);


--
-- Name: discoveries discoveries_pkey; Type: CONSTRAINT; Schema: public; Owner: airflow
--

ALTER TABLE ONLY public.discoveries
    ADD CONSTRAINT discoveries_pkey PRIMARY KEY (insight_key);


--
-- Name: discovery_eval_log discovery_eval_log_pkey; Type: CONSTRAINT; Schema: public; Owner: airflow
--

ALTER TABLE ONLY public.discovery_eval_log
    ADD CONSTRAINT discovery_eval_log_pkey PRIMARY KEY (eval_key);


--
-- Name: llm_eval_log llm_eval_log_pkey; Type: CONSTRAINT; Schema: public; Owner: airflow
--

ALTER TABLE ONLY public.llm_eval_log
    ADD CONSTRAINT llm_eval_log_pkey PRIMARY KEY (eval_key);


--
-- Name: bridge_artist_genre bridge_artist_genre_artist_key_fkey; Type: FK CONSTRAINT; Schema: jason; Owner: airflow
--

ALTER TABLE ONLY jason.bridge_artist_genre
    ADD CONSTRAINT bridge_artist_genre_artist_key_fkey FOREIGN KEY (artist_key) REFERENCES jason.dim_artist(artist_key);


--
-- Name: bridge_artist_genre bridge_artist_genre_genre_key_fkey; Type: FK CONSTRAINT; Schema: jason; Owner: airflow
--

ALTER TABLE ONLY jason.bridge_artist_genre
    ADD CONSTRAINT bridge_artist_genre_genre_key_fkey FOREIGN KEY (genre_key) REFERENCES jason.dim_genre(genre_key);


--
-- Name: dim_library dim_library_track_key_fkey; Type: FK CONSTRAINT; Schema: jason; Owner: airflow
--

ALTER TABLE ONLY jason.dim_library
    ADD CONSTRAINT dim_library_track_key_fkey FOREIGN KEY (track_key) REFERENCES jason.dim_track(track_key);


--
-- Name: fact_play_event fact_play_event_artist_key_fkey; Type: FK CONSTRAINT; Schema: jason; Owner: airflow
--

ALTER TABLE ONLY jason.fact_play_event
    ADD CONSTRAINT fact_play_event_artist_key_fkey FOREIGN KEY (artist_key) REFERENCES jason.dim_artist(artist_key);


--
-- Name: fact_play_event fact_play_event_date_key_fkey; Type: FK CONSTRAINT; Schema: jason; Owner: airflow
--

ALTER TABLE ONLY jason.fact_play_event
    ADD CONSTRAINT fact_play_event_date_key_fkey FOREIGN KEY (date_key) REFERENCES jason.dim_date(dim_date_key);


--
-- Name: fact_play_event fact_play_event_track_key_fkey; Type: FK CONSTRAINT; Schema: jason; Owner: airflow
--

ALTER TABLE ONLY jason.fact_play_event
    ADD CONSTRAINT fact_play_event_track_key_fkey FOREIGN KEY (track_key) REFERENCES jason.dim_track(track_key);


--
-- Name: bridge_artist_genre bridge_artist_genre_artist_key_fkey; Type: FK CONSTRAINT; Schema: kelly; Owner: airflow
--

ALTER TABLE ONLY kelly.bridge_artist_genre
    ADD CONSTRAINT bridge_artist_genre_artist_key_fkey FOREIGN KEY (artist_key) REFERENCES kelly.dim_artist(artist_key);


--
-- Name: bridge_artist_genre bridge_artist_genre_genre_key_fkey; Type: FK CONSTRAINT; Schema: kelly; Owner: airflow
--

ALTER TABLE ONLY kelly.bridge_artist_genre
    ADD CONSTRAINT bridge_artist_genre_genre_key_fkey FOREIGN KEY (genre_key) REFERENCES kelly.dim_genre(genre_key);


--
-- Name: dim_library dim_library_track_key_fkey; Type: FK CONSTRAINT; Schema: kelly; Owner: airflow
--

ALTER TABLE ONLY kelly.dim_library
    ADD CONSTRAINT dim_library_track_key_fkey FOREIGN KEY (track_key) REFERENCES kelly.dim_track(track_key);


--
-- Name: fact_play_event fact_play_event_artist_key_fkey; Type: FK CONSTRAINT; Schema: kelly; Owner: airflow
--

ALTER TABLE ONLY kelly.fact_play_event
    ADD CONSTRAINT fact_play_event_artist_key_fkey FOREIGN KEY (artist_key) REFERENCES kelly.dim_artist(artist_key);


--
-- Name: fact_play_event fact_play_event_date_key_fkey; Type: FK CONSTRAINT; Schema: kelly; Owner: airflow
--

ALTER TABLE ONLY kelly.fact_play_event
    ADD CONSTRAINT fact_play_event_date_key_fkey FOREIGN KEY (date_key) REFERENCES kelly.dim_date(dim_date_key);


--
-- Name: fact_play_event fact_play_event_track_key_fkey; Type: FK CONSTRAINT; Schema: kelly; Owner: airflow
--

ALTER TABLE ONLY kelly.fact_play_event
    ADD CONSTRAINT fact_play_event_track_key_fkey FOREIGN KEY (track_key) REFERENCES kelly.dim_track(track_key);


--
-- Name: SCHEMA jason; Type: ACL; Schema: -; Owner: airflow
--

GRANT USAGE ON SCHEMA jason TO spotify_readonly;


--
-- Name: SCHEMA kelly; Type: ACL; Schema: -; Owner: airflow
--

GRANT USAGE ON SCHEMA kelly TO spotify_readonly;


--
-- Name: TABLE bridge_artist_genre; Type: ACL; Schema: jason; Owner: airflow
--

GRANT SELECT ON TABLE jason.bridge_artist_genre TO spotify_readonly;


--
-- Name: TABLE dim_artist; Type: ACL; Schema: jason; Owner: airflow
--

GRANT SELECT ON TABLE jason.dim_artist TO spotify_readonly;


--
-- Name: TABLE dim_date; Type: ACL; Schema: jason; Owner: airflow
--

GRANT SELECT ON TABLE jason.dim_date TO spotify_readonly;


--
-- Name: TABLE dim_genre; Type: ACL; Schema: jason; Owner: airflow
--

GRANT SELECT ON TABLE jason.dim_genre TO spotify_readonly;


--
-- Name: TABLE dim_library; Type: ACL; Schema: jason; Owner: airflow
--

GRANT SELECT ON TABLE jason.dim_library TO spotify_readonly;


--
-- Name: TABLE dim_track; Type: ACL; Schema: jason; Owner: airflow
--

GRANT SELECT ON TABLE jason.dim_track TO spotify_readonly;


--
-- Name: TABLE fact_play_event; Type: ACL; Schema: jason; Owner: airflow
--

GRANT SELECT ON TABLE jason.fact_play_event TO spotify_readonly;


--
-- Name: TABLE bridge_artist_genre; Type: ACL; Schema: kelly; Owner: airflow
--

GRANT SELECT ON TABLE kelly.bridge_artist_genre TO spotify_readonly;


--
-- Name: TABLE dim_artist; Type: ACL; Schema: kelly; Owner: airflow
--

GRANT SELECT ON TABLE kelly.dim_artist TO spotify_readonly;


--
-- Name: TABLE dim_date; Type: ACL; Schema: kelly; Owner: airflow
--

GRANT SELECT ON TABLE kelly.dim_date TO spotify_readonly;


--
-- Name: TABLE dim_genre; Type: ACL; Schema: kelly; Owner: airflow
--

GRANT SELECT ON TABLE kelly.dim_genre TO spotify_readonly;


--
-- Name: TABLE dim_library; Type: ACL; Schema: kelly; Owner: airflow
--

GRANT SELECT ON TABLE kelly.dim_library TO spotify_readonly;


--
-- Name: TABLE dim_track; Type: ACL; Schema: kelly; Owner: airflow
--

GRANT SELECT ON TABLE kelly.dim_track TO spotify_readonly;


--
-- Name: TABLE fact_play_event; Type: ACL; Schema: kelly; Owner: airflow
--

GRANT SELECT ON TABLE kelly.fact_play_event TO spotify_readonly;


--
-- Name: TABLE llm_eval_log; Type: ACL; Schema: public; Owner: airflow
--

GRANT SELECT ON TABLE public.llm_eval_log TO spotify_readonly;


--
-- Name: DEFAULT PRIVILEGES FOR TABLES; Type: DEFAULT ACL; Schema: jason; Owner: airflow
--

ALTER DEFAULT PRIVILEGES FOR ROLE airflow IN SCHEMA jason GRANT SELECT ON TABLES TO spotify_readonly;


--
-- Name: DEFAULT PRIVILEGES FOR TABLES; Type: DEFAULT ACL; Schema: kelly; Owner: airflow
--

ALTER DEFAULT PRIVILEGES FOR ROLE airflow IN SCHEMA kelly GRANT SELECT ON TABLES TO spotify_readonly;


--
-- PostgreSQL database dump complete
--

\unrestrict 20MVmvrtsUgIlLqftqCmBdvlhv2P3kfJcDn4ZkYAlK9gnqEDncuhfc6nxUelrJz

