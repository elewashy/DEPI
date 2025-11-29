#!/usr/bin/env python3
"""
Smart City IoT Data Streaming - Kafka to HDFS
Processes energy, traffic, bus GPS, waste, and emergency data streams
Matches the SmartCity database schema
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
import logging
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
KAFKA_BROKER = "kafka:9092"
HDFS_NAMENODE = "hdfs://namenode:9000"
TOPICS = ["energy", "traffic", "bus_gps", "waste", "emergency"]
STREAM_DURATION = int(sys.argv[1]) if len(sys.argv) > 1 else 120  # Default 120 seconds

# Create Spark session
spark = SparkSession.builder \
    .appName("SmartCityStreaming") \
    .config("spark.sql.shuffle.partitions", "4") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")
logger.info("Spark session created for Smart City data streaming")

# ========================
# Schemas matching SmartCity DB
# ========================

# energy_consumption schema
energy_schema = StructType([
    StructField("date_key", IntegerType()),
    StructField("time_key", StringType()),
    StructField("building_id", StringType()),
    StructField("device_id", StringType()),
    StructField("kwh", DoubleType()),
    StructField("voltage", DoubleType()),
    StructField("current", DoubleType()),
    StructField("quality_flag", StringType()),
    StructField("timestamp", StringType())
])

# traffic schema
traffic_schema = StructType([
    StructField("date_key", IntegerType()),
    StructField("time_key", StringType()),
    StructField("zone_id", StringType()),
    StructField("device_id", StringType()),
    StructField("vehicle_count", IntegerType()),
    StructField("avg_speed_kmh", DoubleType()),
    StructField("timestamp", StringType())
])

# bus_gps schema
bus_gps_schema = StructType([
    StructField("date_key", IntegerType()),
    StructField("time_key", StringType()),
    StructField("bus_id", StringType()),
    StructField("route_id", StringType()),
    StructField("zone_id", StringType()),
    StructField("lat", DoubleType()),
    StructField("lon", DoubleType()),
    StructField("speed_kmh", DoubleType()),
    StructField("occupancy_est", IntegerType()),
    StructField("timestamp", StringType())
])

# waste_collection schema
waste_schema = StructType([
    StructField("date_key", IntegerType()),
    StructField("time_key", StringType()),
    StructField("zone_id", StringType()),
    StructField("building_id", StringType()),
    StructField("container_id", StringType()),
    StructField("fill_level_percent", IntegerType()),
    StructField("truck_id", StringType()),
    StructField("timestamp", StringType())
])

# emergency_calls schema
emergency_schema = StructType([
    StructField("call_id", StringType()),
    StructField("date_key", IntegerType()),
    StructField("time_key", StringType()),
    StructField("zone_id", StringType()),
    StructField("building_id", StringType()),
    StructField("event_type_id", StringType()),
    StructField("priority_level", StringType()),
    StructField("reported_at", StringType()),
    StructField("resolved_at", StringType()),
    StructField("response_time_minutes", IntegerType()),
    StructField("timestamp", StringType())
])

schemas = {
    "energy": energy_schema,
    "traffic": traffic_schema,
    "bus_gps": bus_gps_schema,
    "waste": waste_schema,
    "emergency": emergency_schema
}


def enrich_energy(df):
    """Add analytics columns for energy data"""
    return df \
        .withColumn("hour", substring(col("time_key"), 1, 2).cast("int")) \
        .withColumn("is_peak_hour", when((col("hour") >= 8) & (col("hour") <= 18), 1).otherwise(0)) \
        .withColumn("is_high_consumption", when(col("kwh") > 15, 1).otherwise(0)) \
        .withColumn("voltage_status", 
            when(col("voltage") < 210, "LOW")
            .when(col("voltage") > 250, "HIGH")
            .otherwise("NORMAL"))


def enrich_traffic(df):
    """Add analytics columns for traffic data"""
    return df \
        .withColumn("hour", substring(col("time_key"), 1, 2).cast("int")) \
        .withColumn("congestion_level",
            when(col("vehicle_count") > 100, "HEAVY")
            .when(col("vehicle_count") > 60, "MODERATE")
            .otherwise("LIGHT")) \
        .withColumn("is_rush_hour", 
            when(((col("hour") >= 7) & (col("hour") <= 9)) | 
                 ((col("hour") >= 17) & (col("hour") <= 19)), 1).otherwise(0))


def enrich_bus_gps(df):
    """Add analytics columns for bus GPS data"""
    return df \
        .withColumn("hour", substring(col("time_key"), 1, 2).cast("int")) \
        .withColumn("occupancy_level",
            when(col("occupancy_est") > 80, "FULL")
            .when(col("occupancy_est") > 50, "CROWDED")
            .when(col("occupancy_est") > 20, "MODERATE")
            .otherwise("EMPTY")) \
        .withColumn("is_delayed", when(col("speed_kmh") < 15, 1).otherwise(0))


def enrich_waste(df):
    """Add analytics columns for waste data"""
    return df \
        .withColumn("hour", substring(col("time_key"), 1, 2).cast("int")) \
        .withColumn("collection_needed", when(col("fill_level_percent") > 80, 1).otherwise(0)) \
        .withColumn("fill_status",
            when(col("fill_level_percent") > 90, "CRITICAL")
            .when(col("fill_level_percent") > 70, "HIGH")
            .when(col("fill_level_percent") > 40, "MEDIUM")
            .otherwise("LOW"))


def enrich_emergency(df):
    """Add analytics columns for emergency data"""
    return df \
        .withColumn("hour", substring(col("time_key"), 1, 2).cast("int")) \
        .withColumn("response_status",
            when(col("response_time_minutes") <= 5, "EXCELLENT")
            .when(col("response_time_minutes") <= 15, "GOOD")
            .when(col("response_time_minutes") <= 30, "ACCEPTABLE")
            .otherwise("DELAYED")) \
        .withColumn("is_critical", when(col("priority_level") == "Critical", 1).otherwise(0))


enrichment_functions = {
    "energy": enrich_energy,
    "traffic": enrich_traffic,
    "bus_gps": enrich_bus_gps,
    "waste": enrich_waste,
    "emergency": enrich_emergency
}


def process_stream(topic, schema):
    """Process a single topic stream to HDFS"""
    logger.info(f"Processing {topic} stream from Kafka: {KAFKA_BROKER}")
    
    # Read from Kafka
    df = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", KAFKA_BROKER) \
        .option("subscribe", topic) \
        .option("startingOffsets", "earliest") \
        .option("failOnDataLoss", "false") \
        .load()
    
    # Parse JSON
    parsed = df.select(
        from_json(col("value").cast("string"), schema).alias("data")
    ).select("data.*")
    
    # Apply enrichment
    enrich_func = enrichment_functions.get(topic)
    if enrich_func:
        enriched = enrich_func(parsed)
    else:
        enriched = parsed
    
    # Add processing metadata
    enriched = enriched \
        .withColumn("processing_time", current_timestamp()) \
        .withColumn("ingestion_date", current_date())
    
    # HDFS output path
    hdfs_output = f"{HDFS_NAMENODE}/smartcity/{topic}"
    checkpoint_dir = f"/tmp/checkpoint_{topic}"
    
    logger.info(f"Writing {topic} to HDFS: {hdfs_output}")
    
    # Write to HDFS as Parquet with partitioning
    query = enriched.writeStream \
        .format("parquet") \
        .option("path", hdfs_output) \
        .option("checkpointLocation", checkpoint_dir) \
        .partitionBy("ingestion_date") \
        .outputMode("append") \
        .trigger(processingTime="10 seconds") \
        .start()
    
    return query


# Start streaming for all topics
logger.info("=" * 80)
logger.info("🏙️  Smart City Data Streaming Pipeline")
logger.info("=" * 80)
logger.info(f"Kafka Broker: {KAFKA_BROKER}")
logger.info(f"HDFS NameNode: {HDFS_NAMENODE}")
logger.info(f"Topics: {TOPICS}")
logger.info(f"Stream Duration: {STREAM_DURATION} seconds")
logger.info("=" * 80)

queries = []
for topic in TOPICS:
    try:
        query = process_stream(topic, schemas[topic])
        queries.append(query)
        logger.info(f"✓ {topic} stream started")
    except Exception as e:
        logger.error(f"✗ Failed to start {topic} stream: {e}")

logger.info("")
logger.info(f"All streams active. Processing data for {STREAM_DURATION} seconds...")
logger.info("")

# Run for specified duration
import time
time.sleep(STREAM_DURATION)

logger.info("Stopping all streams...")
for query in queries:
    try:
        query.stop()
    except Exception as e:
        logger.error(f"Error stopping query: {e}")

logger.info("")
logger.info("=" * 80)
logger.info("Verifying HDFS output...")
logger.info("=" * 80)

# Verify data was written
total_records = 0
for topic in TOPICS:
    try:
        hdfs_path = f"{HDFS_NAMENODE}/smartcity/{topic}"
        written_df = spark.read.parquet(hdfs_path)
        count = written_df.count()
        total_records += count
        logger.info(f"✓ {topic}: {count:,} records written to HDFS")
        if count > 0:
            logger.info(f"  Sample {topic} data:")
            written_df.select(written_df.columns[:6]).show(3, truncate=False)
    except Exception as e:
        logger.warning(f"✗ {topic}: No data yet - {e}")

logger.info("")
logger.info("=" * 80)
logger.info(f"Smart City streaming pipeline completed!")
logger.info(f"Total records written: {total_records:,}")
logger.info("=" * 80)

spark.stop()
