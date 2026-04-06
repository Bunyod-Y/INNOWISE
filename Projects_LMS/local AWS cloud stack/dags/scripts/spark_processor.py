import sys
import argparse
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

def process_bike_metrics(input_file: str, output_dir: str) -> None:
    """
    Uses PySpark to calculate departure and return counts per station.
    
    Args:
        input_file (str): Path to the input CSV file.
        output_dir (str): Directory to save the aggregated metrics CSV.
    """
    spark = SparkSession.builder \
        .appName("HelsinkiBikeMetrics") \
        .master("local[*]") \
        .getOrCreate()

    # Read the CSV file
    df = spark.read.csv(input_file, header=True, inferSchema=True)

    # Metric 3.1: Group by Departure Station
    departure_counts = df.groupBy("Departure station name") \
                         .agg(F.count("*").alias("total_departures")) \
                         .withColumnRenamed("Departure station name", "station_name")

    # Metric 3.2: Group by Return Station
    return_counts = df.groupBy("Return station name") \
                      .agg(F.count("*").alias("total_returns")) \
                      .withColumnRenamed("Return station name", "station_name")

    # Join the two metrics on station name
    station_metrics = departure_counts.join(return_counts, on="station_name", how="outer").fillna(0)

    # Save to a single CSV file
    station_metrics.coalesce(1).write.csv(
        output_dir, 
        header=True, 
        mode="overwrite"
    )
    
    spark.stop()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True, help="Input CSV file path")
    parser.add_argument('--output', required=True, help="Output directory path")
    args = parser.parse_args()
    
    process_bike_metrics(args.input, args.output)