# INNOWISE — Data Engineering Apprenticeship

Coursework and hands-on projects completed during the Innowise data engineering apprenticeship. Each folder is a self-contained task covering a different part of the modern data stack: Python fundamentals, SQL analytics, Spark, orchestration, cloud emulation, and end-to-end streaming architectures.

Most projects run locally with Docker Compose. The repository is designed as a learning portfolio rather than one deployable production system, so each folder should be treated as an independent project with its own services, dependencies, and entry point.

## What this repository demonstrates

This repository shows the progression from writing standalone data-processing code to building distributed data platforms:

1. **Application foundations** — Python, SOLID principles, file parsing, CLI design, and SQLite.
2. **Analytical foundations** — SQL joins, aggregations, grouping, filtering, and business-oriented queries.
3. **Distributed processing** — rebuilding SQL-style transformations with PySpark DataFrames and window functions.
4. **Orchestration** — scheduling, dependencies, sensors, branching, and dataset-driven Airflow workflows.
5. **Cloud-style pipelines** — emulating services such as S3, Lambda, and DynamoDB locally.
6. **Data architecture** — combining APIs, queues, caches, data lakes, Spark, warehouses, monitoring, and streaming sinks.

The main learning goal is not only to make each service run, but to understand why every component exists and what problem it solves.

## Contents

| Folder | What it is | Stack | Main concept |
|---|---|---|---|
| `Python_LMS/` | Student and room analytics CLI with pluggable loaders, SQLite storage, and JSON/XML exporters | Python, SQLite, argparse | Clean architecture and dependency inversion |
| `sql-task/` | Analytical queries over the Sakila/DVD-rental schema, including top actors, rental activity, and revenue analysis | PostgreSQL | Translating business questions into SQL |
| `PySpark_LMS/` | Sakila analytics reimplemented with DataFrame joins, aggregations, and window functions | PySpark | Distributed transformation patterns |
| `SNOWFLAKE/` | Tasty Bytes walkthrough covering databases, schemas, warehouses, time travel, Snowpark, and a Streamlit app | Snowflake SQL, Snowpark, Streamlit | Cloud data warehouse fundamentals |
| `airflow/` | Two chained DAGs: a sensor/branch/clean pipeline that publishes a Dataset, followed by a Dataset-triggered Postgres loader | Airflow, Astro CLI, pandas, PostgreSQL | Workflow orchestration and data-aware scheduling |
| `Projects_LMS/log_alert_system/` | Chunked CSV log processor using pluggable alert rules for fatal-error detection | Python, pandas, Docker | Memory-aware batch processing and extensible rules |
| `Projects_LMS/local AWS cloud stack/` | Helsinki city-bike pipeline using locally emulated S3, Lambda, DynamoDB, Spark, and Airflow | LocalStack, boto3, PySpark, Airflow | Reproducible cloud-service development |
| `Architectures LMS (In-game purchases)/` | Purchase API feeding a durable queue, raw data lake, Spark transformation, and PostgreSQL warehouse | FastAPI, RabbitMQ, PySpark, PostgreSQL | Event-driven ingestion and lake-to-warehouse ETL |
| `Architectures_LMS_Music_store/` | Batch ETL joining listening events from a queue with user profiles from a document store | RabbitMQ, MongoDB, PySpark, PostgreSQL | Multi-source integration and polyglot persistence |
| `Architectures LMS (Crowd-investing platform)/` | Async investment API with caching and metrics, feeding Structured Streaming and multiple storage systems | FastAPI, Redis, Kafka, Spark Structured Streaming, Cassandra, MySQL, Prometheus | Real-time architecture, fan-out, and observability |

## How to read the architecture projects

A useful way to understand the larger projects is to follow the data from producer to consumer.

### 1. Data producer

The producer is usually an API or an event generator. Its responsibility is to accept or create business events such as purchases, listening activity, or investments.

### 2. Message broker

RabbitMQ or Kafka separates the producer from downstream processing. The API can publish an event without waiting for Spark or the database to finish processing it.

This decoupling provides:

- buffering when consumers are temporarily unavailable;
- independent scaling of producers and consumers;
- clearer service boundaries;
- a durable hand-off between system components.

### 3. Raw storage or operational database

Raw events may be stored in a data lake, document database, or another operational store before transformation. Keeping raw data allows transformations to be rerun and makes debugging easier.

### 4. Processing layer

PySpark handles joins, cleaning, aggregation, enrichment, and schema transformation. Batch jobs process bounded datasets, while Structured Streaming continuously processes newly arriving records.

### 5. Serving layer

PostgreSQL, MySQL, Cassandra, DynamoDB, or another destination stores processed data for analytics or application access. The destination is selected according to the access pattern rather than using one database for every workload.

### 6. Orchestration and monitoring

Airflow controls execution order, retries, dependencies, and schedules. Prometheus exposes system metrics so that service health and processing behavior can be observed.

## Running a project

Because every folder is independent, first open the selected project and inspect its local files:

```bash
cd "<project folder>"
ls
```

Look for:

- `README.md` or project-specific notes;
- `docker-compose.yml` or `compose.yml`;
- `requirements.txt` or `pyproject.toml`;
- `.env.example`;
- an entry point such as `app.py`, `etl_pipeline.py`, `spark_etl.py`, or `src/main.py`.

### Typical Docker workflow

```bash
cd "<project folder>"
docker compose config
docker compose up -d --build
docker compose ps
docker compose logs -f
```

`docker compose config` validates the Compose file before services start. `docker compose ps` shows container status, and `docker compose logs -f` is usually the fastest way to identify startup or connection problems.

To stop the project:

```bash
docker compose down
```

To remove project volumes and rebuild stored data from scratch:

```bash
docker compose down -v
```

> Removing volumes deletes data stored by the project containers. Use this only when a clean reset is intended.

### Typical local Python workflow

For projects that run partly outside Docker:

```bash
python -m venv .venv

# Windows PowerShell
.venv\Scripts\Activate.ps1

# Linux or macOS
source .venv/bin/activate

pip install -r requirements.txt
python <entry-point>.py
```

Do not assume that every project uses the same entry point. Check the folder contents and Compose configuration first.

## Suggested learning order

For someone studying the repository, the following order provides a gradual increase in complexity:

1. `Python_LMS/`
2. `sql-task/`
3. `PySpark_LMS/`
4. `Projects_LMS/log_alert_system/`
5. `airflow/`
6. `Projects_LMS/local AWS cloud stack/`
7. `Architectures LMS (In-game purchases)/`
8. `Architectures_LMS_Music_store/`
9. `Architectures LMS (Crowd-investing platform)/`
10. `SNOWFLAKE/`

For each project, try to answer these questions:

- What business event or dataset enters the system?
- Which component owns the raw data?
- Where is validation performed?
- Which transformations are applied?
- How are failures retried or recovered?
- Is processing batch, streaming, or a combination of both?
- Where is the final data served?
- What would need to change before production deployment?

## Themes covered

- Batch versus streaming ingestion
- Message brokers as a decoupling and buffering layer
- Data lake to warehouse ETL with Spark
- Workflow orchestration and data-aware scheduling in Airflow
- Polyglot persistence across relational, document, wide-column, and key-value stores
- Cloud services emulated locally for reproducible development
- Clean architecture with abstract interfaces, dependency inversion, and pluggable rules
- Containerized local environments for multi-service systems
- Observability through logs and metrics

## Learning notes: local demo versus production system

These projects intentionally prioritize learning and reproducibility. A production implementation would usually require additional controls, including:

- secrets stored in a secrets manager rather than committed configuration;
- explicit schema contracts and data-quality checks;
- idempotent consumers and duplicate-event handling;
- dead-letter queues for repeatedly failing messages;
- checkpointing and recovery for streaming jobs;
- automated tests and CI pipelines;
- role-based access control and network restrictions;
- centralized logging, metrics, dashboards, and alerts;
- infrastructure-as-code and environment-specific configuration;
- documented service-level objectives and recovery procedures.

Understanding these gaps is part of the exercise: a working local pipeline proves the flow, while production engineering focuses on reliability, security, maintainability, and operational control.
