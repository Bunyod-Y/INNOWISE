import os
import re
import pandas as pd
from datetime import datetime
from airflow import DAG, Dataset
from airflow.decorators import task, task_group
from airflow.operators.bash import BashOperator
from airflow.operators.python import BranchPythonOperator
from airflow.sensors.filesystem import FileSensor

# ASTRO CLI PATHS: 'include' is mapped to /usr/local/airflow/include
BASE_PATH = "/usr/local/airflow/include"
INPUT_FILE = os.path.join(BASE_PATH, "input", "input_data.csv")
OUTPUT_FILE = os.path.join(BASE_PATH, "output", "processed_data.csv")

# Trigger Dataset
processed_dataset = Dataset(f"file://{OUTPUT_FILE}")

default_args = {
    'owner': 'airflow',
    'start_date': datetime(2024, 1, 1),
    'catchup': False,
}

with DAG(
    dag_id='data_processing_dag',
    default_args=default_args,
    schedule='@daily',
    description='Sensor -> Branch -> Clean -> Dataset',
) as dag:

    # 1. Sensor
    wait_for_file = FileSensor(
        task_id='wait_for_input_file',
        filepath=INPUT_FILE,
        fs_conn_id='fs_default', 
        poke_interval=10,
        timeout=600,
        mode='poke'
    )

    # 2. Branch Logic
    def check_file_empty():
        try:
            # Check if file exists and has content
            if os.stat(INPUT_FILE).st_size == 0:
                 return 'log_empty_file'
            
            df = pd.read_csv(INPUT_FILE)
            if df.empty:
                return 'log_empty_file'
            return 'processing_tasks.replace_nulls'
        except Exception:
            return 'log_empty_file'

    branch_task = BranchPythonOperator(
        task_id='check_if_empty',
        python_callable=check_file_empty
    )

    # 3.1 Empty Path
    log_empty = BashOperator(
        task_id='log_empty_file',
        bash_command='echo "File is empty" >> /usr/local/airflow/logs/empty_log.txt'
    )

    # 3.2 Processing Group
    @task_group(group_id='processing_tasks')
    def processing_tasks():
        
        @task
        def replace_nulls():
            df = pd.read_csv(INPUT_FILE)
            df.fillna("-", inplace=True)
            df.to_csv(os.path.join(BASE_PATH, "output", "temp_1.csv"), index=False)

        @task
        def sort_data():
            df = pd.read_csv(os.path.join(BASE_PATH, "output", "temp_1.csv"))
            if 'created_date' in df.columns:
                df['created_date'] = pd.to_datetime(df['created_date'])
                df.sort_values(by='created_date', inplace=True)
            df.to_csv(os.path.join(BASE_PATH, "output", "temp_2.csv"), index=False)

        @task(outlets=[processed_dataset])
        def clean_content():
            df = pd.read_csv(os.path.join(BASE_PATH, "output", "temp_2.csv"))
            
            def clean_text(text):
                if not isinstance(text, str): return str(text)
                return re.sub(r'[^\w\s\.,!?;:-]', '', text)

            if 'content' in df.columns:
                df['content'] = df['content'].apply(clean_text)
            
            df.to_csv(OUTPUT_FILE, index=False)
            
            # Cleanup temps
            for f in ["temp_1.csv", "temp_2.csv"]:
                p = os.path.join(BASE_PATH, "output", f)
                if os.path.exists(p): os.remove(p)

        replace_nulls() >> sort_data() >> clean_content()

    wait_for_file >> branch_task
    branch_task >> log_empty
    branch_task >> processing_tasks()