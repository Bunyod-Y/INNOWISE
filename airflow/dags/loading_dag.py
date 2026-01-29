import os
import pandas as pd
from datetime import datetime
from airflow import DAG, Dataset
from airflow.decorators import task
from airflow.providers.postgres.hooks.postgres import PostgresHook

# ASTRO PATHS
BASE_PATH = "/usr/local/airflow/include"
INPUT_FILE = os.path.join(BASE_PATH, "output", "processed_data.csv")

processed_dataset = Dataset(f"file://{INPUT_FILE}")

default_args = {
    'owner': 'airflow',
    'start_date': datetime(2024, 1, 1),
    'catchup': False,
}

with DAG(
    dag_id='postgres_loader_dag',
    default_args=default_args,
    schedule=[processed_dataset],
    description='Load CSV to Postgres',
) as dag:

    @task
    def create_table_if_not_exists():
        hook = PostgresHook(postgres_conn_id='postgres_dw')
        sql = """
            CREATE TABLE IF NOT EXISTS reviews (
                created_date DATE,
                rating INT,
                content TEXT
            );
        """
        hook.run(sql)

    @task
    def load_data():
        df = pd.read_csv(INPUT_FILE)
        
        # Using SQLAlchemy engine from the hook for easier Pandas insertion
        hook = PostgresHook(postgres_conn_id='postgres_dw')
        engine = hook.get_sqlalchemy_engine()
        
        # 'replace' will drop the table and recreate it. 
        # Use 'append' if you want to keep history.
        df.to_sql('reviews', engine, if_exists='replace', index=False)
        print(f"Loaded {len(df)} rows into Postgres.")

    create_table_if_not_exists() >> load_data()