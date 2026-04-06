import pika
import pymongo
import json
from pyspark.sql import SparkSession
from pyspark.sql.functions import monotonically_increasing_id

print("1. EXTRACT: Pulling Data from RabbitMQ...")
# Connect to RabbitMQ and pull all waiting messages
credentials = pika.PlainCredentials('admin', 'adminpassword')
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost', 5672, '/', credentials))
channel = connection.channel()

events = []
while True:
    # Pull messages one by one until the queue is empty
    method_frame, header_frame, body = channel.basic_get(queue='listening_history', auto_ack=True)
    if method_frame:
        events.append(json.loads(body))
    else:
        break
connection.close()

if len(events) == 0:
    print("No events found in RabbitMQ. Please run app_simulator.py first!")
    exit()

print(f" -> Extracted {len(events)} streaming events.")

print("2. EXTRACT: Pulling User Profiles from MongoDB...")
# Connect to MongoDB
mongo_client = pymongo.MongoClient("mongodb://admin:adminpassword@localhost:27017/")
db = mongo_client["music_platform"]
users_data = list(db["users"].find({}, {"_id": 0})) # Exclude the internal MongoDB ID
print(f" -> Extracted {len(users_data)} user profiles.")

print("3. INITIALIZE: Starting PySpark Engine (Simulating Databricks)...")
spark = SparkSession.builder \
    .appName("MusicPlatform_ETL") \
    .config("spark.jars.packages", "org.postgresql:postgresql:42.6.0") \
    .getOrCreate()
spark.sparkContext.setLogLevel("WARN")

# Load python lists into PySpark DataFrames
events_df = spark.createDataFrame(events)
users_df = spark.createDataFrame(users_data)

print("4. TRANSFORM: Building Star Schema for Data Warehouse...")

# Build Dimension Table: Users
dim_users = users_df.select("user_id", "name", "subscription", "country").distinct()

# Build Dimension Table: Songs (Extract unique songs and generate a unique ID)
dim_songs = events_df.select("song_name", "genre").distinct() \
    .withColumn("song_id", monotonically_increasing_id())

# Build Fact Table: Streams (Join events with dim_songs to map the song_id)
fact_streams = events_df.join(dim_songs, on="song_name", how="left") \
    .select("event_id", "user_id", "song_id", "listen_duration_seconds", "timestamp")

print("5. LOAD: Writing structured tables to PostgreSQL (Simulating Azure Synapse)...")
jdbc_url = "jdbc:postgresql://localhost:5432/synapse_dwh"
db_properties = {"user": "admin", "password": "adminpassword", "driver": "org.postgresql.Driver"}

# Write tables
dim_users.write.jdbc(url=jdbc_url, table="dim_users", mode="overwrite", properties=db_properties)
dim_songs.write.jdbc(url=jdbc_url, table="dim_songs", mode="overwrite", properties=db_properties)
fact_streams.write.jdbc(url=jdbc_url, table="fact_streams", mode="overwrite", properties=db_properties)

print("SUCCESS! ETL Pipeline Complete. Data is ready for BI Dashboards.")
