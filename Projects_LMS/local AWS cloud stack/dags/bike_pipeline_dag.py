import os
import boto3
from datetime import datetime
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator

# LocalStack S3 Configuration
AWS_ENDPOINT = os.getenv("AWS_ENDPOINT_URL", "http://localstack:4566")
AWS_REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
RAW_BUCKET = "helsinki-bike-raw"
METRICS_BUCKET = "helsinki-bike-metrics"

def get_s3_client():
    """Returns a boto3 S3 client configured for LocalStack."""
    return boto3.client(
        's3',
        endpoint_url=AWS_ENDPOINT,
        aws_access_key_id='test',
        aws_secret_access_key='test',
        region_name=AWS_REGION
    )

def get_lambda_client():
    """Returns a boto3 Lambda client configured for LocalStack."""
    return boto3.client(
        'lambda',
        endpoint_url=AWS_ENDPOINT,
        aws_access_key_id='test',
        aws_secret_access_key='test',
        region_name=AWS_REGION
    )

def setup_s3_buckets(**kwargs):
    """Ensures S3 buckets exist in LocalStack before uploading."""
    s3 = get_s3_client()
    for bucket in [RAW_BUCKET, METRICS_BUCKET]:
        try:
            s3.head_bucket(Bucket=bucket)
        except Exception:
            s3.create_bucket(Bucket=bucket)

def upload_raw_to_s3(file_name: str, **kwargs):
    """Uploads the raw monthly CSV file to S3."""
    s3 = get_s3_client()
    local_path = f"/opt/airflow/data/split_months/{file_name}"
    s3_key = f"raw/{file_name}"
    
    s3.upload_file(local_path, RAW_BUCKET, s3_key)
    return s3_key

def upload_metrics_to_s3(file_name: str, **kwargs):
    """Finds the Spark output CSV and uploads it to S3."""
    s3 = get_s3_client()
    # Spark writes to a directory with partitioned parts. We find the actual CSV file.
    metrics_dir = f"/opt/airflow/data/metrics/{file_name}_metrics"
    
    csv_file = None
    for file in os.listdir(metrics_dir):
        if file.endswith(".csv"):
            csv_file = os.path.join(metrics_dir, file)
            break
            
    if csv_file:
        s3_key = f"metrics/{file_name.replace('.csv', '_metrics.csv')}"
        s3.upload_file(csv_file, METRICS_BUCKET, s3_key)
        return s3_key
    raise FileNotFoundError("Spark metrics output CSV not found.")

def invoke_dynamodb_lambda(raw_s3_key: str, metrics_s3_key: str, **kwargs):
    """Directly triggers the AWS Lambda function to load data into DynamoDB."""
    lambda_client = get_lambda_client()
    
    payload = {
        "raw_bucket": RAW_BUCKET,
        "raw_key": raw_s3_key,
        "metrics_bucket": METRICS_BUCKET,
        "metrics_key": metrics_s3_key
    }
    
    # We use RequestResponse to wait for the Lambda to finish (Option A logic)
    import json
    response = lambda_client.invoke(
        FunctionName='LoadBikesToDynamoDB',
        InvocationType='RequestResponse', 
        Payload=json.dumps(payload)
    )
    
    response_payload = json.loads(response['Payload'].read())
    print(f"Lambda Response: {response_payload}")

# Define the DAG
default_args = {
    'owner': 'data_engineer',
    'start_date': datetime(2023, 1, 1),
    'retries': 1,
}

with DAG(
    dag_id='helsinki_bike_processor',
    default_args=default_args,
    schedule_interval=None, # Triggered manually or by a sensor
    catchup=False
) as dag:

    # Let's assume we are processing the May 2016 file
    target_file = "bike_data_2016-05.csv"

    task_setup_buckets = PythonOperator(
        task_id='setup_s3_buckets',
        python_callable=setup_s3_buckets
    )

    task_upload_raw = PythonOperator(
        task_id='upload_raw_s3',
        python_callable=upload_raw_to_s3,
        op_kwargs={'file_name': target_file}
    )

    task_run_spark = BashOperator(
        task_id='run_spark_metrics',
        bash_command=(
            f"python /opt/airflow/dags/scripts/spark_processor.py "
            f"--input /opt/airflow/data/split_months/{target_file} "
            f"--output /opt/airflow/data/metrics/{target_file}_metrics"
        )
    )

    task_upload_metrics = PythonOperator(
        task_id='upload_metrics_s3',
        python_callable=upload_metrics_to_s3,
        op_kwargs={'file_name': target_file}
    )

    task_invoke_lambda = PythonOperator(
        task_id='trigger_dynamodb_lambda',
        python_callable=invoke_dynamodb_lambda,
        op_kwargs={
            'raw_s3_key': f"raw/{target_file}",
            'metrics_s3_key': f"metrics/{target_file.replace('.csv', '_metrics.csv')}"
        }
    )

    # Option A Orchestration Flow: Ensure strict sequential execution
    task_setup_buckets >> task_upload_raw >> task_run_spark >> task_upload_metrics >> task_invoke_lambda