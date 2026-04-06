import os
import boto3
import pandas as pd
import json
from datetime import datetime
from decimal import Decimal

# Configure Boto3 to use LocalStack endpoints
AWS_ENDPOINT = os.getenv("AWS_ENDPOINT_URL", "http://host.docker.internal:4566")
AWS_REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1")

s3_client = boto3.client('s3', endpoint_url=AWS_ENDPOINT, region_name=AWS_REGION)
dynamodb = boto3.resource('dynamodb', endpoint_url=AWS_ENDPOINT, region_name=AWS_REGION)

def lambda_handler(event, context):
    """
    Triggered by Airflow. Reads S3 files, calculates metrics, and saves to DynamoDB.
    """
    print(f"Received event: {event}")
    
    raw_bucket = event.get('raw_bucket')
    raw_key = event.get('raw_key')
    
    if not raw_bucket or not raw_key:
        return {"statusCode": 400, "body": "Missing S3 bucket or key in event."}

    try:
        # 1. Read Raw CSV from S3 into Pandas
        obj = s3_client.get_object(Bucket=raw_bucket, Key=raw_key)
        df = pd.read_csv(obj['Body'])
        
        # 2. Data Cleaning & Feature Engineering
        df['Departure'] = pd.to_datetime(df['Departure'], errors='coerce')
        df = df.dropna(subset=['Departure', 'Distance (m)', 'Duration (sec.)'])
        
        # Calculate Speed (meters per second)
        # Avoid division by zero
        df['Speed (m/s)'] = df.apply(
            lambda row: row['Distance (m)'] / row['Duration (sec.)'] if row['Duration (sec.)'] > 0 else 0, 
            axis=1
        )
        
        # Mock Temperature (since it's missing from the bike dataset)
        import random
        df['Temperature (C)'] = [random.uniform(10.0, 25.0) for _ in range(len(df))]
        
        # Extract Date for daily grouping
        df['Date'] = df['Departure'].dt.date
        
        # 3. Calculate Daily Metrics (Requirement 6)
        daily_metrics = df.groupby('Date').agg(
            avg_distance=('Distance (m)', 'mean'),
            avg_duration=('Duration (sec.)', 'mean'),
            avg_speed=('Speed (m/s)', 'mean'),
            avg_temp=('Temperature (C)', 'mean')
        ).reset_index()
        
        # 4. Save to DynamoDB
        table = dynamodb.Table('BikeDailyMetrics')
        
        with table.batch_writer() as batch:
            for _, row in daily_metrics.iterrows():
                # DynamoDB requires floats to be cast to Decimals
                item = {
                    'Date': str(row['Date']),
                    'AvgDistance': Decimal(str(round(row['avg_distance'], 2))),
                    'AvgDuration': Decimal(str(round(row['avg_duration'], 2))),
                    'AvgSpeed': Decimal(str(round(row['avg_speed'], 2))),
                    'AvgTemperature': Decimal(str(round(row['avg_temp'], 2))),
                    'ProcessedAt': datetime.utcnow().isoformat()
                }
                batch.put_item(Item=item)
                
        print(f"Successfully processed and loaded {len(daily_metrics)} daily records to DynamoDB.")
        
        return {
            "statusCode": 200,
            "body": json.dumps(f"Processed {raw_key} successfully!")
        }
        
    except Exception as e:
        print(f"Error processing file: {e}")
        return {"statusCode": 500, "body": str(e)}