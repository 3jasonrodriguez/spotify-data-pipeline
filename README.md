# Spotify Data Pipeline

> A personal data engineering portfolio project — ingesting, transforming, and visualizing 10+ years of Spotify listening history using a modern cloud data stack.

[![Dashboard Demo](https://img.youtube.com/vi/12h5bisPd_8/maxresdefault.jpg)](https://www.youtube.com/watch?v=12h5bisPd_8)
*Click to watch a short demo of the Streamlit dashboard*

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Design Decisions](#design-decisions)
- [Key Pivots](#key-pivots)
- [Personal Project Constraints](#personal-project-constraints)
- [A Note on AI Assistance](#a-note-on-ai-assistance)
- [Tech Stack](#tech-stack)

---

## Overview

This project analyzes ~127,000 personal Spotify streaming events spanning 2015–2026. Raw data is ingested from the Spotify Web API and a personal listening history export, enriched with genre metadata from MusicBrainz, transformed through a medallion architecture, and served through an interactive Streamlit dashboard.

The goal was to build something that demonstrates hands-on proficiency with the tools central to data engineering roles today — not just to process data, but to make real infrastructure decisions, respond to real constraints, and document the reasoning behind them.

### How It Started

The project began with six questions I wanted to answer from my own listening data:

- Top 10 most time-listened tracks of all time
- Listening history over time by genre
- Top 10 tracks played during work hours
- Total listening time per year
- Saved library tracks never played
- Longest consecutive listening streak by track

As the data got cleaner and the schema took shape, the analysis evolved. New questions emerged from what the data actually showed, and the dashboard shifted to reflect that. The six above were the starting point of curiosity — not the final scope.

---

## Architecture

![Architecture Diagram](docs/architecture.png)

### Medallion Layers

| Layer | Storage | Role |
|-------|---------|------|
| **Bronze** | AWS S3 | Raw JSON from Spotify API, streaming history export, MusicBrainz genre data |
| **Silver** | AWS Athena | SQL transformations over S3 via Glue-catalogued tables |
| **Gold** | PostgreSQL | Star schema — serves the Streamlit dashboard |

### Gold Layer — Star Schema

```
fact_play_event
├── dim_date          (year, month, day, hour, is_weekend, is_work_hours)
├── dim_track         (track metadata — UNIONed from streaming history + library)
├── dim_artist        (artist metadata — same UNION pattern)
├── dim_genre         (MusicBrainz-sourced genre reference)
├── dim_library       (saved library tracks; enables "never played" analysis)
└── bridge_artist_genre  (many-to-many: artist ↔ genre)
```

### Infrastructure

| Component | Detail |
|-----------|--------|
| **EC2** | t3.small, Amazon Linux 2023, 20GB EBS |
| **Docker Compose** | Airflow + PostgreSQL co-hosted on the EC2 instance |
| **Airflow** | LocalExecutor — no Redis, no Celery worker |
| **S3** | Raw data store; Hive-partitioned JSONL |
| **Glue** | Crawlers populate `spotify_pipeline_raw` for Athena querying |
| **Athena** | Serverless SQL over S3; silver layer transformation engine |
| **IAM** | `spotify-pipeline-svc` service account with least-privilege S3 policy |
| **Streamlit** | Dashboard served from EC2; queries in `sql/streamlit_queries.py` |

---

## Design Decisions

### S3 Partitioning Strategy

Most sources use standard Hive-style partitioning (`year=YYYY/month=MM/day=DD`). Streaming history uses year-only partitioning (`year=YYYY`).

All analytical questions are year-scoped, so month and day partitions add path complexity without any query benefit — Athena would scan at the year level regardless. A single `load_to_s3()` helper accepts an optional `year` parameter to handle both patterns without separate upload functions.

### Dimension Table Scope — UNION Strategy

Early on, `dim_artist` and `dim_track` were populated only from streaming history. This caused a large volume of unmapped foreign keys in `fact_play_event` because streaming history records often lack stable Spotify IDs — they contain names but no identifier.

The fix was to UNION both the streaming history and the saved library when building these dimensions. Tracks in the library that never appear in streaming are captured. Records missing IDs are represented with `NULL` rather than dropped. This significantly improved fact table join coverage.

### Idempotency — Truncate vs. ON CONFLICT

The pipeline is designed to be safely re-runnable:

- **Fact tables** — truncate-and-reload. The entire table is cleared and repopulated on each run. Facts are always recomputable from source.
- **Dimension tables** — `ON CONFLICT (unique_key) DO NOTHING`. Dimensions accumulate over time; existing records are skipped, new ones are added.

### Airflow Configuration

**Why LocalExecutor?** The pipeline started with CeleryExecutor, which requires a Redis broker and a separate Celery worker container. There's no genuine parallelism need here — tasks run sequentially. CeleryExecutor added memory overhead and operational complexity without benefit. Dropping it freed meaningful RAM on the t3.small and simplified `docker-compose.yml`.

Key parameter choices:

| Parameter | Value | Reason |
|-----------|-------|--------|
| `max_active_runs` | `1` | Prevents concurrent runs that would race on truncate-reload tables |
| `catchup` | `False` | Pipeline is run on-demand; backfill would reprocess unintended windows |
| Task retries | Per-task on API tasks | Handles transient rate limit errors without failing the full DAG |

### EC2 Instance Selection

The project started on local Docker Desktop (Windows/WSL), which hit memory limits under Airflow + PostgreSQL and became unstable. That was the forcing function for moving to EC2.

Instance evaluation:

| Instance | RAM | Decision |
|----------|-----|----------|
| t3.micro | 1 GB | Insufficient — Airflow scheduler + PostgreSQL + active task exceeded limit |
| **t3.small** | **2 GB** | **Chosen — workable with LocalExecutor; cost-effective for steady-state** |
| c7i-flex.large | 4 GB | Used temporarily during heavy development; not cost-justified for steady-state |

Demanding runs (e.g., full MusicBrainz enrichment) may require temporarily scaling up. EC2 User Data scripts were explored to automate Docker bootstrapping on new instances so the setup can be reproduced without manual configuration.

### Hosting Strategy — Keeping It Self-Contained

A deliberate decision was made to run the full stack — Airflow, PostgreSQL, Streamlit — on a single EC2 instance rather than using managed services like RDS or MWAA, and to not publicly host the Streamlit dashboard.

**Why not Streamlit Cloud?** Streamlit Cloud cannot directly connect to a PostgreSQL instance running inside a private EC2 environment. Making that work would require either exposing the database publicly (a security risk), setting up a VPN or bastion host, or migrating PostgreSQL to a managed service like RDS with the appropriate network rules — all of which add meaningful cost and complexity for a personal project. Keeping everything on EC2 avoids all of that.

**How the dashboard is accessed:** The Streamlit app runs on the EC2 instance and is accessed locally via SSH tunneling. A tunnel forwards the remote port to localhost, so the dashboard runs in a local browser without exposing any ports to the public internet:

```bash
ssh -L 8501:localhost:8501 ec2-user@<your-ec2-ip>
```

**The tradeoff:** The dashboard isn't publicly shareable via a URL. For a portfolio project this is an accepted constraint — the demo video linked at the top of this README serves as the artifact for sharing.

### Spotify API Changes — Adapting Mid-Project

The Spotify Web API introduced breaking changes in February 2026 that directly impacted the pipeline:

- `popularity` and `followers` fields were removed from artist objects without prior announcement
- Playlist item access was restricted to owned playlists only

This required defensive coding patterns throughout: `.get()` for all optional fields, explicit `NULL` handling, and schema checks at extraction. The broader lesson: treat external API responses as inherently unstable.

One other quirk: OAuth requires `http://127.0.0.1:8888/callback` exactly — not `localhost` — even though they resolve to the same address. Spotify's developer portal does string matching on the redirect URI.

### Genre Enrichment — MusicBrainz and Its Limitations

When Spotify deprecated genre data on artist objects, MusicBrainz was adopted as the enrichment source. It works, but introduced its own constraints:

- **Rate limiting** — 1-second minimum delay between requests, enforced in the enrichment script
- **User-Agent requirement** — requests without a descriptive header are rejected
- **Two-step lookup** — search for artist by name to get a MusicBrainz ID, then fetch the full record to retrieve genre tags
- **Fuzzy name matching** — artist names between Spotify and MusicBrainz often differ (punctuation, featured artist notation, alternate spellings). `difflib.SequenceMatcher` with a ~0.85 similarity threshold handles this without false positives

**Known limitation:** MusicBrainz genre coverage is incomplete. Niche, regional, or emerging artists often have no tags, resulting in `NULL` genre assignments. This is an accepted gap — genre-based analytics exclude these artists rather than misattribute them.

### Multi-User Schema Design

The schema was built with multi-user extensibility in mind. A `user_id` dimension scopes all fact and dimension data to a specific account. A second user could be onboarded by providing their credentials and running the pipeline with their `user_id` — no schema restructuring required.

### Streamlit Dashboard

All queries live in `sql/streamlit_queries.py` rather than inline in `app.py`. This keeps the dashboard code readable and makes it possible to tune or replace a query without touching UI logic.

Visualizations are built programmatically — chart configurations are derived from query results rather than hardcoded, which lets the same patterns scale across different time ranges or subsets without duplication.

---

## Key Pivots

| Before | After | Driver |
|--------|-------|--------|
| Docker Desktop (local, Windows/WSL) | AWS EC2 t3.small | WSL memory limits under Airflow + PostgreSQL |
| CeleryExecutor + Redis + worker | LocalExecutor | No real parallelism needed; Celery added overhead |
| Spotify genre data | MusicBrainz API + fuzzy matching | Spotify deprecated genre fields Feb 2026 |
| Uniform `year/month/day` partitioning | Year-only for streaming history | Analytical questions are year-scoped |
| Streaming history only for dim tables | UNION with saved library | Large volume of missing fact table mappings |
| Naive inserts | Truncate-reload (facts) / `ON CONFLICT DO NOTHING` (dims) | Safe rerunnability |
| Managed services (RDS, MWAA) | Self-hosted Docker on EC2 | Cost + learning depth |

---

## Personal Project Constraints

Several production patterns were intentionally omitted. These are explicit tradeoffs, not gaps.

| Pattern | Rationale |
|---------|-----------|
| CI/CD pipeline | Solo development; Git used for version control only |
| Incremental / CDC loading | Full refresh is acceptable at this data volume |
| Data quality / validation layer | Quality enforced via NULL handling and idempotency patterns |
| Multi-AZ / high availability | Single EC2 instance; downtime is acceptable |
| Complete genre coverage | MusicBrainz gaps accepted; niche artists may have NULL genres |
| Automated testing | Validation via row count comparisons and manual spot checks |
| Publicly hosted dashboard | Streamlit Cloud requires direct DB access or managed hosting; SSH tunneling is sufficient for personal use |

---

## A Note on AI Assistance

Claude (Anthropic) was used as a collaborative assistant throughout this project — with a deliberate constraint: Claude was explicitly asked not to write code unless diagnosing a specific error. This was a conscious learning strategy.

I intentionally told Claude to allow me to grow as a developer and work through design decisions, constraints, and roadblocks myself.

**Estimated code ownership: ~85% written independently.** The remaining ~15% reflects targeted suggestions for specific patterns (e.g., the `NextToken` pagination loop, `execute_values` batch insert structure) that were then integrated, adapted, and tested manually. No full modules or DAG files were AI-generated.

How Claude was used:
- Discussing architecture options and tradeoffs before writing code
- Explaining AWS service behaviors (Athena pagination, Glue crawlers, IAM scoping)
- Diagnosing specific errors — e.g., why `cursor.rowcount` is unreliable with `execute_values`
- Identifying logic gaps — e.g., the dimension table scope issue causing missing fact mappings
- Reviewing design decisions and surfacing unconsidered edge cases

---

## Tech Stack

| Category | Technologies |
|----------|-------------|
| Language | Python 3.x, SQL (Athena / PostgreSQL) |
| Orchestration | Apache Airflow (LocalExecutor, Docker Compose on EC2) |
| Cloud | AWS EC2, S3, Athena, Glue, IAM |
| Database | PostgreSQL (Airflow metadata + `spotify` gold schema) |
| APIs | Spotify Web API (OAuth), MusicBrainz API |
| Dashboard | Streamlit + Altair |
| Libraries | psycopg2, boto3, spotipy, difflib, pandas |
| Source Control | GitHub |

---

*Built by Jason Rodriguez · Charlotte, NC*
