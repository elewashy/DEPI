from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import *

spark = SparkSession.builder \
    .appName("QuickStreamTest") \
    .master("local[4]") \
    .getOrCreate()

# Energy schema
energy_schema = StructType([
    StructField("date_key", IntegerType()),
    StructField("time_key", IntegerType()),
    StructField("building_id", StringType()),
    StructField("device_id", StringType()),
    StructField("kwh", DoubleType()),
    StructField("voltage", DoubleType()),
    StructField("current", DoubleType()),
    StructField("quality_flag", IntegerType())
])

# Read from Kafka
df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "kafka:9092") \
    .option("subscribe", "energy") \
    .option("startingOffsets", "latest") \
    .load()

# Parse JSON
parsed_df = df.select(
    from_json(col("value").cast("string"), energy_schema).alias("data")
).select("data.*")

# Show data to console
query = parsed_df.writeStream \
    .outputMode("append") \
    .format("console") \
    .option("truncate", "false") \
    .option("numRows", 5) \
    .trigger(processingTime="5 seconds") \
    .start()

query.awaitTermination(15)
query.stop()
spark.stop()
print("\n✓ Spark Streaming working - processed energy data from Kafka")
