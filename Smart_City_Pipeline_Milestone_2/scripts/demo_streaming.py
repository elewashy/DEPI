#!/usr/bin/env python3
"""
Smart City Real-Time Streaming Demo
Shows live IoT sensor data being processed in real-time
Matches the SmartCity database schema
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
import logging
import sys

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# Configuration
DEMO_DURATION = int(sys.argv[1]) if len(sys.argv) > 1 else 60

# Create Spark session
spark = SparkSession.builder \
    .appName("SmartCityStreamingDemo") \
    .config("spark.sql.shuffle.partitions", "2") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")

# Schemas matching SmartCity DB
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

traffic_schema = StructType([
    StructField("date_key", IntegerType()),
    StructField("time_key", StringType()),
    StructField("zone_id", StringType()),
    StructField("device_id", StringType()),
    StructField("vehicle_count", IntegerType()),
    StructField("avg_speed_kmh", DoubleType()),
    StructField("timestamp", StringType())
])

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

logger.info("")
logger.info("=" * 80)
logger.info("  🏙️  SMART CITY REAL-TIME DATA PIPELINE - LIVE VIEW")
logger.info("=" * 80)
logger.info("")
logger.info("  Reading from Kafka: kafka:9092")
logger.info("  Topics: energy, traffic, bus_gps, waste, emergency")
logger.info(f"  Demo Duration: {DEMO_DURATION} seconds")
logger.info("")

# Read and parse energy data
energy_df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "kafka:9092") \
    .option("subscribe", "energy") \
    .option("startingOffsets", "latest") \
    .option("failOnDataLoss", "false") \
    .load()

energy_parsed = energy_df.select(
    from_json(col("value").cast("string"), energy_schema).alias("data"),
    col("timestamp").alias("kafka_ts")
).select("data.*", "kafka_ts")

energy_enriched = energy_parsed \
    .withColumn("process_time", current_timestamp()) \
    .withColumn("consumption_status", 
        when(col("kwh") > 30, "⚡ VERY HIGH")
        .when(col("kwh") > 15, "⚡ HIGH")
        .otherwise("✓ Normal")) \
    .withColumn("voltage_status", 
        when(col("voltage") < 210, "⚠️ LOW")
        .when(col("voltage") > 250, "⚠️ HIGH")
        .otherwise("✓ OK"))

# Read and parse traffic data
traffic_df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "kafka:9092") \
    .option("subscribe", "traffic") \
    .option("startingOffsets", "latest") \
    .option("failOnDataLoss", "false") \
    .load()

traffic_parsed = traffic_df.select(
    from_json(col("value").cast("string"), traffic_schema).alias("data"),
    col("timestamp").alias("kafka_ts")
).select("data.*", "kafka_ts")

traffic_enriched = traffic_parsed \
    .withColumn("process_time", current_timestamp()) \
    .withColumn("congestion", 
        when(col("vehicle_count") > 100, "🔴 HEAVY")
        .when(col("vehicle_count") > 60, "🟡 MODERATE")
        .otherwise("🟢 LIGHT"))

# Read and parse bus GPS data
bus_df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "kafka:9092") \
    .option("subscribe", "bus_gps") \
    .option("startingOffsets", "latest") \
    .option("failOnDataLoss", "false") \
    .load()

bus_parsed = bus_df.select(
    from_json(col("value").cast("string"), bus_gps_schema).alias("data"),
    col("timestamp").alias("kafka_ts")
).select("data.*", "kafka_ts")

bus_enriched = bus_parsed \
    .withColumn("process_time", current_timestamp()) \
    .withColumn("occupancy_status",
        when(col("occupancy_est") > 80, "🔴 FULL")
        .when(col("occupancy_est") > 50, "🟡 CROWDED")
        .otherwise("🟢 AVAILABLE"))

# Read and parse waste data
waste_df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "kafka:9092") \
    .option("subscribe", "waste") \
    .option("startingOffsets", "latest") \
    .option("failOnDataLoss", "false") \
    .load()

waste_parsed = waste_df.select(
    from_json(col("value").cast("string"), waste_schema).alias("data"),
    col("timestamp").alias("kafka_ts")
).select("data.*", "kafka_ts")

waste_enriched = waste_parsed \
    .withColumn("process_time", current_timestamp()) \
    .withColumn("fill_status",
        when(col("fill_level_percent") > 90, "🔴 CRITICAL")
        .when(col("fill_level_percent") > 70, "🟡 HIGH")
        .otherwise("🟢 OK"))

# Read and parse emergency data
emergency_df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "kafka:9092") \
    .option("subscribe", "emergency") \
    .option("startingOffsets", "latest") \
    .option("failOnDataLoss", "false") \
    .load()

emergency_parsed = emergency_df.select(
    from_json(col("value").cast("string"), emergency_schema).alias("data"),
    col("timestamp").alias("kafka_ts")
).select("data.*", "kafka_ts")

emergency_enriched = emergency_parsed \
    .withColumn("process_time", current_timestamp()) \
    .withColumn("priority_icon",
        when(col("priority_level") == "Critical", "🚨")
        .when(col("priority_level") == "High", "⚠️")
        .when(col("priority_level") == "Medium", "📋")
        .otherwise("📝"))

# Aggregations
energy_agg = energy_enriched \
    .groupBy(
        window(col("process_time"), "30 seconds"),
        col("building_id")
    ) \
    .agg(
        count("*").alias("readings"),
        round(avg("kwh"), 2).alias("avg_kwh"),
        round(max("kwh"), 2).alias("max_kwh"),
        round(avg("voltage"), 1).alias("avg_voltage")
    ) \
    .orderBy(col("window.start").desc(), col("avg_kwh").desc())

traffic_agg = traffic_enriched \
    .groupBy(
        window(col("process_time"), "30 seconds"),
        col("zone_id")
    ) \
    .agg(
        round(avg("vehicle_count"), 0).alias("avg_vehicles"),
        round(avg("avg_speed_kmh"), 1).alias("avg_speed"),
        max("vehicle_count").alias("max_vehicles")
    ) \
    .orderBy(col("window.start").desc(), col("avg_vehicles").desc())

logger.info("🎬 Starting streaming queries...")
logger.info(f"   Duration: {DEMO_DURATION} seconds")
logger.info("=" * 80)
logger.info("")

queries = []

# Energy stream
q1 = energy_enriched.select(
    "building_id", "device_id", 
    round(col("kwh"), 2).alias("kwh"),
    round(col("voltage"), 1).alias("voltage"),
    "consumption_status", "voltage_status"
).writeStream \
    .outputMode("append") \
    .format("console") \
    .option("truncate", False) \
    .option("numRows", 5) \
    .trigger(processingTime="10 seconds") \
    .queryName("energy_stream") \
    .start()
queries.append(q1)

# Traffic stream
q2 = traffic_enriched.select(
    "zone_id", "device_id", "vehicle_count",
    round(col("avg_speed_kmh"), 1).alias("speed_kmh"),
    "congestion"
).writeStream \
    .outputMode("append") \
    .format("console") \
    .option("truncate", False) \
    .option("numRows", 5) \
    .trigger(processingTime="10 seconds") \
    .queryName("traffic_stream") \
    .start()
queries.append(q2)

# Bus GPS stream
q3 = bus_enriched.select(
    "bus_id", "route_id", "zone_id",
    round(col("speed_kmh"), 1).alias("speed"),
    "occupancy_est", "occupancy_status"
).writeStream \
    .outputMode("append") \
    .format("console") \
    .option("truncate", False) \
    .option("numRows", 5) \
    .trigger(processingTime="10 seconds") \
    .queryName("bus_stream") \
    .start()
queries.append(q3)

# Emergency stream
q4 = emergency_enriched.select(
    "call_id", "zone_id", "event_type_id",
    "priority_level", "priority_icon",
    "response_time_minutes"
).writeStream \
    .outputMode("append") \
    .format("console") \
    .option("truncate", False) \
    .option("numRows", 5) \
    .trigger(processingTime="10 seconds") \
    .queryName("emergency_stream") \
    .start()
queries.append(q4)

# Energy aggregation
q5 = energy_agg.writeStream \
    .outputMode("complete") \
    .format("console") \
    .option("truncate", False) \
    .option("numRows", 8) \
    .trigger(processingTime="15 seconds") \
    .queryName("energy_agg") \
    .start()
queries.append(q5)

logger.info("✅ All streaming queries started!")
logger.info("")
logger.info("📊 Showing:")
logger.info("  1. Energy consumption (every 10s)")
logger.info("  2. Traffic sensors (every 10s)")
logger.info("  3. Bus GPS tracking (every 10s)")
logger.info("  4. Emergency calls (every 10s)")
logger.info("  5. Energy aggregations (every 15s)")
logger.info("")

# Run for specified duration
import time
time.sleep(DEMO_DURATION)

logger.info("")
logger.info("=" * 80)
logger.info("  ⏹️  Stopping streaming demo")
logger.info("=" * 80)

for q in queries:
    try:
        q.stop()
    except:
        pass

spark.stop()
logger.info("✓ Demo completed!")
