from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.window import Window

# Initialize Spark
spark = SparkSession.builder.appName("PagilaAnalysis").getOrCreate()

# Load CSVs
def load_df(name):
    return spark.read.csv(f"{name}.csv", header=True, inferSchema=True)

category = load_df("category")
film = load_df("film")
film_category = load_df("film_category")
actor = load_df("actor")
film_actor = load_df("film_actor")
inventory = load_df("inventory")
rental = load_df("rental")
payment = load_df("payment")
customer = load_df("customer")
address = load_df("address")
city = load_df("city")

print("--- TASK 1: Movies per category ---")
category.join(film_category, "category_id").groupBy("name").count().orderBy(F.desc("count")).show()

print("--- TASK 2: Top 10 Actors by Rental Count ---")
actor.join(film_actor, "actor_id").join(inventory, "film_id").join(rental, "inventory_id") \
    .groupBy("first_name", "last_name").count().orderBy(F.desc("count")).limit(10).show()

print("--- TASK 3: Most profitable category ---")
category.join(film_category, "category_id").join(inventory, "film_id").join(rental, "inventory_id").join(payment, "rental_id") \
    .groupBy("name").agg(F.sum("amount").alias("total")).orderBy(F.desc("total")).limit(1).show()

print("--- TASK 4: Movies NOT in inventory ---")
film.join(inventory, "film_id", "left_anti").select("title").show()

print("--- TASK 5: Top 3 Actors in 'Children' category (with ties) ---")
child_actors = actor.join(film_actor, "actor_id").join(film_category, "film_id").join(category, "category_id") \
    .filter(F.col("name") == "Children").groupBy("first_name", "last_name").count()
res5 = child_actors.withColumn("rank", F.dense_rank().over(Window.orderBy(F.desc("count")))).filter(F.col("rank") <= 3)
res5.show()

print("--- TASK 6: Active/Inactive Customers by City ---")
city.join(address, "city_id").join(customer, "address_id") \
    .groupBy("city").agg(F.sum(F.when(F.col("active") == 1, 1).otherwise(0)).alias("active"), 
                         F.sum(F.when(F.col("active") == 0, 1).otherwise(0)).alias("inactive")) \
    .orderBy(F.desc("inactive")).show()

print("--- TASK 7: Highest rental hours for cities starting with 'a' or '-' ---")
def get_top_cat(pattern):
    return category.join(film_category, "category_id").join(inventory, "film_id").join(rental, "inventory_id") \
        .join(customer, "customer_id").join(address, "address_id").join(city, "city_id") \
        .filter(F.col("city").like(pattern)) \
        .withColumn("hours", (F.unix_timestamp("return_date") - F.unix_timestamp("rental_date")) / 3600) \
        .groupBy("name").agg(F.sum("hours").alias("total_hours")).orderBy(F.desc("total_hours")).limit(1)

print("Pattern 'a%':")
get_top_cat("a%").show()
print("Pattern '%-%':")
get_top_cat("%-%").show()