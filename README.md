# INNOWISE — Data Engineering Apprenticeship

Coursework and hands-on projects completed during the Innowise data engineering apprenticeship. Each folder is a self-contained task covering a different part of the modern data stack: Python fundamentals, SQL analytics, Spark, orchestration, cloud emulation, and end-to-end streaming architectures.

Most projects run locally via `docker-compose`.

## Contents

| Folder | What it is | Stack |
|---|---|---|
| `Python_LMS/` | Student/room analytics CLI built on SOLID principles — pluggable JSON loaders, SQLite storage, JSON/XML exporters | Python, SQLite, argparse |
| `sql-task/` | Analytical queries over the Sakila/DVD-rental schema (top actors, rental hours by city, revenue by category) | PostgreSQL |
| `PySpark_LMS/` | The same Sakila analytics reimplemented with DataFrame joins, aggregations and window functions | PySpark |
| `SNOWFLAKE/` | 20-step Tasty Bytes walkthrough: databases, schemas, warehouses, time travel, plus a Streamlit app | Snowflake SQL, Snowpark, Streamlit |
| `airflow/` | Two chained DAGs — a sensor/branch/clean pipeline that publishes a Dataset, and a Dataset-triggered Postgres loader | Airflow (Astro CLI), pandas, Postgres |
| `Projects_LMS/log_alert_system/` | Chunked log processor that evaluates pluggable alert rules (fatal errors per minute, per hour per bundle) over large CSVs | Python, pandas, Docker |
| `Projects_LMS/local AWS cloud stack/` | Helsinki city-bike pipeline on an emulated AWS: S3 buckets, a Lambda loading into DynamoDB, Spark aggregations, orchestrated by Airflow | LocalStack, boto3, PySpark, Airflow |
| `Architectures LMS (In-game purchases)/` | Purchase API → durable queue → raw data lake → Spark transform → Postgres warehouse | FastAPI, RabbitMQ, PySpark, Postgres |
| `Architectures_LMS_Music_store/` | Batch ETL joining listening events from a queue with user profiles from a document store | RabbitMQ, MongoDB, PySpark, Postgres |
| `Architectures LMS (Crowd-investing platform)/` | Async investment API with caching and metrics, feeding a Structured Streaming job that fans out to Cassandra and MySQL | FastAPI, Redis, Kafka, Spark Streaming, Cassandra, Prometheus |

## Running a project

```bash
cd "<project folder>"
docker-compose up -d
pip install -r requirements.txt   # where present
```

Then run the project's entry point (`app.py`, `etl_pipeline.py`, `spark_etl.py`, or `src/main.py` depending on the task). Services are configured for `localhost` defaults.

## Themes covered

- Batch vs. streaming ingestion, and message brokers as a decoupling layer
- Data lake → warehouse ETL with Spark
- Workflow orchestration and data-aware scheduling in Airflow
- Polyglot persistence: relational, document, wide-column, key-value
- Cloud services emulated locally for reproducible development
- Clean architecture: abstract interfaces, dependency inversion, pluggable rules and exporters
