from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import StructType, StructField, StringType, DoubleType

print("Initializing PySpark Streaming Engine...")

# 1. Initialize Spark and pull necessary connector libraries
spark = SparkSession.builder \
    .appName("CrowdInvestingStreaming") \
    .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1,com.datastax.spark:spark-cassandra-connector_2.12:3.4.1,mysql:mysql-connector-java:8.0.33") \
    .config("spark.cassandra.connection.host", "localhost") \
    .config("spark.cassandra.connection.port", "9042") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")

# 2. Define the schema of our incoming Kafka JSON messages
schema = StructType([
    StructField("user_id", StringType(), True),
    StructField("franchise_id", StringType(), True),
    StructField("amount", DoubleType(), True),
    StructField("currency", StringType(), True),
    StructField("timestamp", StringType(), True)
])

# 3. Connect to Kafka and read the stream
print("Connecting to Kafka...")
kafka_df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "localhost:9092") \
    .option("subscribe", "investments_topic") \
    .option("startingOffsets", "earliest") \
    .load()

# Parse the binary Kafka value into our structured JSON schema
parsed_df = kafka_df.selectExpr("CAST(value AS STRING)") \
    .select(from_json(col("value"), schema).alias("data")) \
    .select("data.*")

# 4. Define Output Sink 1: Console (So we can see it working in the terminal)
console_query = parsed_df.writeStream \
    .outputMode("append") \
    .format("console") \
    .start()

# 5. Define Output Sink 2: Cassandra (High-volume ledger)
cassandra_query = parsed_df.writeStream \
    .outputMode("append") \
    .format("org.apache.spark.sql.cassandra") \
    .option("keyspace", "crowd_keyspace") \
    .option("table", "investments_history") \
    .option("checkpointLocation", "/tmp/spark_checkpoints/cassandra") \
    .start()

# 6. Define Output Sink 3: MySQL (Relational analytics)
def write_to_mysql(batch_df, batch_id):
    batch_df.write \
        .format("jdbc") \
        .option("url", "jdbc:mysql://localhost:3306/crowd_invest_db") \
        .option("driver", "com.mysql.cj.jdbc.Driver") \
        .option("dbtable", "investments_ledger") \
        .option("user", "admin") \
        .option("password", "adminpassword") \
        .mode("append") \
        .save()

mysql_query = parsed_df.writeStream \
    .foreachBatch(write_to_mysql) \
    .option("checkpointLocation", "/tmp/spark_checkpoints/mysql") \
    .start()

print("Streaming Pipeline is ACTIVE. Waiting for incoming data from Kafka...")
spark.streams.awaitAnyTermination()