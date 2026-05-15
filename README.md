# DJ Data

> A personal Spotify analytics platform built from scratch over three months — a full modern data stack powered by a decade of real listening history, extended to two users, and driven by an agentic AI layer that thinks, queries, evaluates, and discovers.

[![Dashboard Demo](https://img.youtube.com/vi/12h5bisPd_8/maxresdefault.jpg)](https://www.youtube.com/watch?v=12h5bisPd_8)
*Click to watch a demo of the DJ Data platform*

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Feature Walkthrough](#feature-walkthrough)
- [Evolution of the Project](#evolution-of-the-project)
- [Technical Deep Dives](#technical-deep-dives)
- [Limitations and Known Issues](#limitations-and-known-issues)
- [Replication Guide](#replication-guide)
- [Learnings and Reflections](#learnings-and-reflections)
- [How Claude Was Used](#how-claude-was-used)

---

## Overview

It started as a simple question: what does my Spotify streaming history actually look like as data? The answer turned out to be far more interesting than expected — and far more buildable than I initially believed. What began as a personal ETL pipeline grew into a medallion architecture on AWS, an Apache Airflow orchestration layer, a PostgreSQL gold layer modeled as a star schema, an interactive Streamlit dashboard, and finally a three-tier LLM system that generates SQL, judges its own output, and autonomously surfaces insights neither user thought to look for.

This is my first personal project. I built it deliberately — writing the code myself with Claude as a design partner and code reviewer, not a shortcut. Every architectural decision, every prompt engineering iteration, every debugging session was mine to own. That mattered to me. Building something real, in a domain I love, with tools that pushed me — that's what this project is.

---

## Architecture

A medallion architecture on AWS — raw data flows from S3 through Glue and Athena into a PostgreSQL star schema, orchestrated by Airflow and served through Streamlit, all running on a single EC2 instance.

![Pipeline Architecture](docs/diagrams/dj-data-pipeline-diagram.png)

### Bronze Layer — Raw Ingestion

Spotify history exports, Spotify API metadata, and MusicBrainz genre enrichment land in S3 — cleansed of PII and partitioned by user and year.

<details>
<summary>Read more</summary>

The bronze layer is the entry point for all raw data. Spotify streaming history arrives as static JSON exports and is lightly cleansed to remove PII before landing in S3. The data is enriched at this stage with additional context from the Spotify API — primarily library and track metadata — and from MusicBrainz, an open music database used to fill the artist and genre relationships that Spotify deprecated from their API.

S3 was chosen as the storage layer for its native integration with Glue and Athena, its flexible partitioning model, and prior familiarity. As the project expanded to a second user, partitions were structured around users from the start — a decision that propagated cleanly through every downstream layer and made cross-user querying straightforward later on.

</details>

---

### Silver Layer — Schema & Transformation

Glue crawlers infer schemas from S3 JSONL and create Athena-queryable tables — no manual table scripts, S3 treated as source of truth.

<details>
<summary>Read more</summary>

The silver layer is built on AWS Glue and Athena. Glue crawlers crawl the S3 bronze data, infer schemas from the stored JSONL files, and automatically create tables available for Athena querying — eliminating the need to write and maintain manual table creation scripts. Athena then queries S3 directly through those tables, keeping the architecture lean by treating S3 as the source of truth rather than introducing another database layer.

Crawlers are run manually in this project, a deliberate tradeoff to conserve AWS resources outside of active development and demonstration. One practical challenge at this layer was handling schema drift — changes in the Spotify API's response structure occasionally required crawler reruns and schema adjustments, a real-world data engineering problem that shaped how the bronze layer stored certain datasets as snapshots rather than appended records.

</details>

---

### Gold Layer — Analytical Model

Python extracts Athena query results and loads them into a PostgreSQL star schema — one fact table, five dimensions, a bridge table, and isolated per-user schemas.

![Star Schema](docs/diagrams/dj-data-star-schema.png)

<details>
<summary>Read more</summary>

The gold layer lives in PostgreSQL, chosen deliberately for hands-on experience with a widely used open-source database after a background primarily in Oracle. Data arrives here via Python scripts that execute Athena queries against the silver layer and insert the results into Postgres using psycopg2.

The data is modeled as a star schema centered on a single fact table — `fact_play_event` — representing one discrete Spotify play event. Surrounding dimension tables cover `dim_track`, `dim_artist`, `dim_date`, `dim_genre`, and `dim_library`, the latter capturing whether a track is saved to a user's library and when. Artist-to-genre relationships are handled through a bridge table, reflecting the many-to-many nature of that relationship.

As the project expanded to a second user, each user was given an isolated Postgres schema containing the same table structure rather than sharing tables with a user column — a cleaner separation that simplified permissioning, querying, and the readonly access model built for the agentic layer later on.

</details>

---

### Orchestration — Apache Airflow

Airflow manages the full ETL flow with explicit task dependencies, a boolean parameter for full vs. lightweight runs, and an on-demand Docker Compose stack separate from the application layer.

<details>
<summary>Read more</summary>

Apache Airflow orchestrates the full pipeline, managing task dependencies and execution order across the ETL flow. DAG tasks cover loading raw streaming history from flat files, and individual loads for each dimension and fact table. Dependencies are explicitly defined in the DAG based on upstream data requirements — dimensions must be populated before the fact table, mirroring standard dimensional modeling load order.

A boolean parameter controls whether the streaming history flat files are reloaded on a given run, allowing a full end-to-end ETL execution when needed or a lighter run that skips the raw file ingestion — a practical design decision for a pipeline where the source files don't change on every run.

Airflow was chosen deliberately for exposure to modern orchestration tooling, building on prior experience with job dependency management in Control-M. The LocalExecutor was selected over alternatives like Celery after finding that heavier executors consumed more resources than the project infrastructure warranted.

Airflow runs on-demand via a separate Docker Compose file, deliberately decoupled from the always-running application stack of Postgres and Streamlit. This separation reflects a practical operational distinction — the ETL pipeline isn't always needed, and being able to spin up the application layer independently for dashboard work or database changes without bringing up the full orchestration stack keeps the infrastructure lean and purposeful.

</details>

---

### Application Layer — Streamlit

Three-page app: custom visualizations dashboard, agentic natural language chat interface, and an autonomous discoveries page — all querying Postgres directly.

<details>
<summary>Read more</summary>

Streamlit serves as the front-facing application layer, hosting three pages — an interactive visualization dashboard, an agentic natural language chat interface for querying the data, and an autonomous discoveries page that surfaces insights neither user thought to ask for. It was chosen for its clean aesthetic and fast iteration cycle, originally scoped to just the visualization page before naturally becoming the home for the agentic layer as the project expanded.

Streamlit connects directly to the PostgreSQL gold layer, keeping the application layer thin and the database as the single source of truth for both the dashboard and the AI-powered query interface.

</details>

---

### Infrastructure — AWS EC2

Full stack on a single `c7i-flex.large` instance — Docker Compose, EC2 User Data bootstrapping, local dev → GitHub → EC2 workflow.

<details>
<summary>Read more</summary>

The project runs entirely on a single EC2 `c7i-flex.large` instance — a deliberate simplicity choice for a personal project that balances cost and compute effectively. Postgres, Streamlit, the MCP server, and Airflow all run on the same instance via Docker Compose, keeping the deployment straightforward without sacrificing the real-world infrastructure experience.

The development workflow follows a clean separation between local and cloud environments — code is written locally, pushed to GitHub, and pulled onto the EC2 instance rather than edited directly on the server. The instance is bootstrapped via EC2 User Data, ensuring the environment is reproducible from a clean start.

</details>

---

## Feature Walkthrough

### Visualizations

A decade of streaming history in one dashboard — KPIs, daily streaming bar chart with drilldown, genre trends, library growth, listening streaks, streams by day of week, top ten tracks, annual hours, and an artist word cloud. Multi-user selector controls the full page.

<details>
<summary>Read more</summary>

The visualizations page is the original core of DJ Data — a fully custom analytics dashboard built on a decade of personal streaming history. A multi-user selector at the top controls the entire page, allowing seamless switching between users.

The page includes: a KPI summary row, a full streaming history bar chart where clicking any day drills down into what was played and for how long, yearly genre trends with multi-genre overlay filtering, library growth over time, listening streaks showing the longest consecutive days a track was played, streaming hours by day of week, top ten most played tracks, annual streaming hours by year, and an artist word cloud.

Genre gaps are acknowledged directly on the page, a transparency decision reflecting known limitations in the MusicBrainz enrichment data.

</details>

---

### DJ Data — Chat Interface

Natural language to SQL — ask questions about your listening history in plain English, get answers with charts. Confidence-aware: the eval layer surfaces when it isn't sure.

![Agentic Loop](docs/diagrams/dj-data-agentic-loop.png)

<details>
<summary>Read more</summary>

The DJ Data page is the agentic analytics layer — a natural language interface for querying a decade of streaming data without writing a single line of SQL. A user scope selector supports querying Jason's data, Kelly's data, or a cross-user comparison.

Six suggested questions offer jumping off points for exploration, alongside an open prompt for freeform questions. DJ Data answers in natural language accompanied by an appropriate chart or table, and is transparent about its confidence — if the evaluation layer flags a low quality answer, the response says so and invites a rephrased question. Questions outside the scope of the database are handled gracefully rather than hallucinated.

</details>

---

### Discoveries

An Airflow DAG lets Claude autonomously explore the database and surface insights nobody asked for — one per user, one cross-user comparison. Explore Further hands off directly to the chat interface.

![Discoveries Flow](docs/diagrams/dj-data-discoveries.png)

<details>
<summary>Read more</summary>

The Discoveries page surfaces insights neither user thought to ask for. A separate Airflow DAG allows Claude to autonomously explore the PostgreSQL database and generate notable findings — presented as individual discoveries for each user and a cross-user comparison discovery. It's the most agentic part of the project: unprompted, exploratory, and driven entirely by what the data actually contains.

The page displays the latest passing discovery per user scope, with a full archive of past discoveries below. Clicking any past discovery opens it in a popover. Clicking **Explore Further** on any discovery auto-populates the DJ Data chat page with the correct user scope and follow-up question — handing off seamlessly to the ask flow.

</details>

---

## Evolution of the Project

DJ Data grew through a series of real pivots — a Spotify API scope limitation that redirected the entire project, a second user added mid-build, a migration from local Docker to EC2, and finally an agentic layer that became the most technically interesting part of the whole thing.

<details>
<summary>Read more</summary>

DJ Data didn't start as what it is today — it grew through a series of pivots, discoveries, and expanding ambitions.

It began with two parallel ideas: analyzing personal Spotify streaming history, and exploring global stream data from genre-based playlists. The project began with six concrete questions to answer from personal listening data: top 10 most played tracks of all time, listening history over time by genre, top 10 tracks played during work hours, total listening time per year, saved library tracks never played, and longest consecutive listening streak by track.

The playlist idea hit an early wall — Spotify's API scope limitations meant the project would be confined to personal library data only. That constraint turned out to be a gift. A decade of personal streaming history is richer and more interesting than aggregated playlist data, and the questions it raised were more meaningful. As the data got cleaner and the schema took shape, new questions emerged from what the data actually showed and the dashboard evolved to reflect that. Those six were the spark — not the final scope.

From there the project grew incrementally. MusicBrainz enrichment was added to fill the genre gap left by Spotify's deprecation of artist and genre fields. Partition schemes were refined along the way — saved tracks moved to a truncate and reload pattern where partitions added no value, while streaming history retained year-based partitions to support the cross-year analytical questions the project was built to answer.

The pipeline was then extended to a second user, requiring a rethink of the schema structure, S3 partitioning, and query scope — a real mid-project requirement change that touched every layer. Shortly after, the local development environment moved to Docker on EC2, bringing the project into the cloud and off a personal laptop.

The final and most significant evolution was the agentic layer — a natural language analytics interface built on top of the existing pipeline. What started as prompt engineering quickly revealed unexpected depth: the level of context, instruction, and iteration required to produce reliable SQL generation and coherent insights was a genuine surprise. More surprising still was the quality of what the model found when given autonomous access to the data — the discoveries it surfaced were insights neither user had thought to look for.

The project closed with a public landing page, a fitting endpoint for something that started as a personal curiosity.

</details>

---

## Technical Deep Dives

### Prompt Engineering

Three distinct prompts — system, judge, and discoveries — each with explicit role definitions, schema context, response format specs, and an assumption-transparency pattern that states reasoning rather than asking clarifying questions.

<details>
<summary>Read more</summary>

The agentic layer is built on three distinct prompts, each carefully structured to produce consistent, reliable output from the model.

The **system prompt** accepts a user scope parameter — Jason, Kelly, or Compare Both — and opens with a behavioral instruction tailored to that scope, telling the model what data it has access to and how to apply it. It then defines the agent's role, specifies the expected response format in detail, and provides explicit guidelines for each component of the response object including the natural language insight, the SQL query, and the chart specification.

The **judge prompt** defines an evaluator role and is given the full database schema as context. It receives the original question, the generated SQL, and the model's response as inputs, scores the answer against a defined rubric, and returns a structured evaluation. The scoring mechanism determines whether DJ Data surfaces the answer confidently or flags it for rephrasing.

The **discoveries prompt** also accepts user scope and schema context, defines an autonomous exploration role, passes in prior discoveries to prevent repetition, and provides detailed instructions for response format including chart spec guidelines and query structure.

A deliberate design decision across all three prompts was the **assumption-transparency pattern** — rather than asking clarifying questions upfront, the model is instructed to make reasonable assumptions on ambiguous terms like "recent" or "trending" and state them explicitly in the response. This was a conscious UX and architecture choice: it keeps the interface clean, tests the model's reasoning capability directly, and produces a more impressive and honest user experience than a back-and-forth clarification flow.

The most surprising aspect of this entire layer was the depth of iteration required to get consistent output. Small changes in phrasing, instruction ordering, and context specificity produced meaningfully different results — a firsthand lesson in how much prompt engineering actually matters in production agentic systems.

</details>

---

### Eval Layer

LLM-as-a-Judge for both SQL quality and discovery interestingness — structured verdicts, Postgres logging, and a regex safety gate at execution time independent of the eval flow.

<details>
<summary>Read more</summary>

The evaluation layer is a two-part system designed to assess both the quality of generated SQL and the interestingness of autonomous discoveries before either reaches the user.

**Judge SQL** receives the original question, user scope, generated SQL, and the natural language response as inputs. It is explicitly told it is evaluating output produced by another LLM call. It assesses whether the SQL is well-formed, performant, applicable to the question, and analytically correct — scoring on a 1-5 rubric where a 3 or higher is required to pass.

**Judge Discovery** evaluates autonomous insights against a different rubric — whether the discovery is genuinely interesting, grounded in the data, and paired with an appropriate chart suggestion. Its passing threshold is intentionally set at 2 or higher, a deliberate calibration to maximize the volume of insights returned initially. That threshold is designed to be raised over time as the discovery quality is observed in practice.

Both judges return a structured verdict dictionary. In the orchestration layer, the `ask` and `discover` functions check the verdict before passing results to Streamlit — passed verdicts are rendered, failed verdicts are handled gracefully in the UI with an appropriate message to the user. All verdicts, passing and failing, are logged to PostgreSQL with their scores and explanations, creating an audit trail for evaluating and improving the system over time.

A separate safety gate lives at the execution layer rather than the eval layer — regex pattern matching in the `execute_sql` tool blocks destructive SQL at the point of execution, keeping data integrity enforcement independent of quality evaluation.

</details>

---

### Error Handling

Graceful failure at every layer — try/except around all API calls, distinct user-facing messages for failed verdicts vs. hard errors, Airflow retries, and verdict logging to Postgres.

<details>
<summary>Read more</summary>

Error handling across DJ Data is designed to fail gracefully at every layer while keeping the user experience clean.

All Anthropic API calls are wrapped in try/except blocks. Failures in the agentic flow — whether from token limits, malformed responses, or execution errors — are logged behind the scenes and surface to the user as "No data for this question" rather than exposing raw errors. Failed judge verdicts follow a separate pattern, surfacing as "DJ Data is not confident in this answer, try rephrasing your question" — keeping the UI predictable regardless of the failure reason.

Airflow DAGs include retry logic with a wait gap between attempts, providing resilience against transient failures in API calls or database connections during pipeline runs. Both the pipeline DAG and the discoveries DAG have thorough logging throughout, giving clear visibility into task execution and failure points within the Airflow UI.

Logging to Postgres captures judge verdicts — both passing and failing — with scores and explanations, providing an audit trail for the agentic layer. There is room to expand structured logging further across the application layer, something identified as a future improvement.

</details>

---

## Limitations and Known Issues

- **Error messaging granularity** — Token limit errors and hard failures currently surface the same user-facing message. More specific error classification is a future improvement.
- **Data freshness** — No explicit freshness indicator on the dashboard. A future extension would surface this in the UI and potentially allow the agentic layer to trigger pipeline runs when recent data is needed.
- **Saved tracks / streaming history gap** — Tracks streamed but never saved may have incomplete metadata, producing genre and artist enrichment gaps.
- **Genre coverage** — MusicBrainz coverage is incomplete for some artists, resulting in known genre gaps acknowledged directly in the dashboard.
- **Manual Glue crawler runs** — Schema changes require a manual crawler rerun; no automated schedule by design.
- **Landing page / Streamlit navigation** — Navigation between the static landing page and the Streamlit app is functional but not seamless.

---

## Replication Guide

### Prerequisites

- AWS account with EC2 and S3 access
- Spotify Developer credentials per user
- Anthropic API credentials
- Docker and Docker Compose
- Python dependencies per `requirements.txt`

### Steps

1. Clone the repository locally and on your EC2 instance
2. Configure Spotify Developer credentials for each user
3. Add your Anthropic API key to the environment configuration
4. Set up AWS credentials and configure your S3 bucket and EC2 instance
5. Configure environment variables and `config.yaml` per the provided templates
6. Spin up the application stack with `make up` and Airflow with `make airflow-up` when needed
7. Run Glue crawlers to build the silver layer tables after initial S3 loads
8. Trigger the Airflow DAG for an initial full pipeline run to populate the gold layer
9. Access Streamlit via SSH tunnel:

```bash
ssh -L 8501:localhost:8501 ec2-user@<your-ec2-ip>
```

> **Note** — Built and tested on a single EC2 `c7i-flex.large` instance. Resource requirements for other instance types have not been tested.

---

## Learnings and Reflections

Building DJ Data meant touching nearly every phase of a modern data pipeline. The LLM layer was the most unexpected — the specificity required in prompts and how small instruction changes produced meaningfully different output was a genuine revelation. Scope creep and perfectionism were real challenges, and learning when to ship was its own skill.

The ending state of the project is impressive considering where it started. That matters.

<details>
<summary>Read more</summary>

Building DJ Data meant touching nearly every phase of a modern data pipeline — ingestion, transformation, modeling, orchestration, cloud infrastructure, application development, and finally an agentic AI layer. That end-to-end ownership was the point, and it delivered.

Throughout the project there was a deliberate curiosity about design at each stage — not just making things work, but asking why a particular pattern or tool was the right choice. That instinct, reinforced by constantly researching best practices, produced better architectural decisions and a deeper understanding of the tradeoffs involved.

The LLM layer was the most unexpected learning. The specificity required in prompts and context — and how meaningfully small changes in instruction affected output quality — was a genuine revelation. Working with language models as engineering components rather than chat interfaces is a different discipline, and building it firsthand made that clear in a way that reading about it never could.

The project also surfaced some honest personal lessons. Perfectionism and scope creep crept in toward the end, and learning when to stop and ship something demonstrable was its own skill. Resource constraints — both compute and time — shaped better decisions than unlimited resources might have. And building in a domain that was personally meaningful made the hard parts worth pushing through.

If anything would be done differently, it would be more user testing beyond personal use. But the priority was always to ship something working, learnable, and real — and that's what DJ Data is.

The ending state of the project is impressive considering where it started. That matters.

</details>

---

## How Claude Was Used

Claude was a design partner, code reviewer, scope manager, and documentation collaborator throughout the build — not a code generator. The agentic layer running in production is a separate relationship entirely: Claude as a runtime engine powering SQL generation, evaluation, and autonomous discovery.

<details>
<summary>Read more</summary>

Claude was a core collaborator throughout the build — but not a shortcut. The relationship was deliberately structured to preserve code ownership and genuine understanding at every step.

During the build, Claude served as a design partner for architectural decisions, an idea reviewer for validating approaches before committing to them, a scope reflector for keeping the project grounded when ambition outpaced resources, a code reviewer for catching issues and suggesting improvements, and a project manager for calling out scope creep before it derailed progress. This documentation was also written collaboratively — the thinking and substance is the author's, the shaping and polish was Claude's.

A deliberate ground rule throughout: Claude was instructed to guide and review rather than implement. Understanding checks were a regular part of the process, ensuring that every piece of code written was owned and explainable, not just functional. The ratio of human to AI written code skews heavily toward the author — and more importantly, the understanding behind it is entirely theirs.

In the running application, Claude plays a different role entirely — it is the runtime engine. The Anthropic API powers the natural language to SQL generation, the judge evaluation layer, and the autonomous discoveries DAG. Claude as a build tool and Claude as a production component are two distinct relationships, and DJ Data is a firsthand demonstration of both.

</details>

---

*Built by Jason Rodriguez · Charlotte, NC*