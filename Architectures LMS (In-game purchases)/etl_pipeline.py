import pika
import json
import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import current_timestamp, col

# ==========================================
# 1. EXTRACT: RabbitMQ -> Local Data Lake
# ==========================================
print("Extracting messages from RabbitMQ...")
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()
channel.queue_declare(queue='gcomm_purchases', durable=True)

messages = []
while True:
    # Pull messages one by one until the queue is empty
    method_frame, header_frame, body = channel.basic_get(queue='gcomm_purchases', auto_ack=True)
    if method_frame:
        messages.append(json.loads(body))
    else:
        break
connection.close()

if not messages:
    print("No new purchases in the queue. Exiting pipeline.")
    exit()

# Save raw data to our "Data Lake" (a local JSON lines file)
data_lake_file = 'data_lake_raw.json'
with open(data_lake_file, 'w') as f:
    for msg in messages:
        f.write(json.dumps(msg) + '\n')

print(f"Successfully extracted {len(messages)} purchase events to Data Lake.\n")

# ==========================================
# 2. TRANSFORM & LOAD: PySpark -> PostgreSQL
# ==========================================
print("Starting PySpark Processing Engine...")

# Initialize Spark and automatically pull the PostgreSQL JDBC driver
spark = SparkSession.builder \
    .appName("gComm_ETL") \
    .config("spark.jars.packages", "org.postgresql:postgresql:42.6.0") \
    .getOrCreate()

# Read the raw data from our Data Lake
df = spark.read.json(data_lake_file)

# Transformations: 
# - Ensure price is a float
# - Filter out bad transactions (price <= 0)
# - Add a timestamp for when this row was processed into the Data Warehouse
clean_df = df.withColumn("price", col("price").cast("double")) \
             .filter(col("price") > 0) \
             .withColumn("dw_processed_at", current_timestamp())

print("\n--- Transformed Data Preview ---")
clean_df.show()

# Load into PostgreSQL Data Warehouse
print("Loading data into PostgreSQL Data Warehouse...")
db_url = "jdbc:postgresql://localhost:5432/gcomm_dw"
db_properties = {
    "user": "admin",
    "password": "adminpassword",
    "driver": "org.postgresql.Driver"
}

# Write the dataframe to a table called 'fact_purchases'
clean_df.write.jdbc(url=db_url, table="fact_purchases", mode="append", properties=db_properties)

print("ETL Pipeline completed successfully! Data is now in your Data Warehouse.")