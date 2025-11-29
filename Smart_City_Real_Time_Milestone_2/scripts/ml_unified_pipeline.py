#!/usr/bin/env python3
"""
Smart City ML - Unified Machine Learning Pipeline
Trains all ML models for the Smart City data platform
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
from pyspark.ml.feature import VectorAssembler, StringIndexer, StandardScaler
from pyspark.ml.regression import RandomForestRegressor, GBTRegressor
from pyspark.ml.classification import RandomForestClassifier, GBTClassifier
from pyspark.ml.evaluation import RegressionEvaluator, MulticlassClassificationEvaluator
from pyspark.ml import Pipeline
import logging
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
KAFKA_BROKER = "kafka:9092"
HDFS_NAMENODE = "hdfs://namenode:9000"
MODEL_BASE_PATH = "/tmp/models"

# Create Spark session
spark = SparkSession.builder \
    .appName("SmartCityUnifiedML") \
    .config("spark.sql.shuffle.partitions", "4") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")

logger.info("")
logger.info("=" * 80)
logger.info("🏙️  SMART CITY UNIFIED MACHINE LEARNING PIPELINE")
logger.info("=" * 80)
logger.info("")

# Schemas
schemas = {
    "energy": StructType([
        StructField("date_key", IntegerType()),
        StructField("time_key", StringType()),
        StructField("building_id", StringType()),
        StructField("device_id", StringType()),
        StructField("kwh", DoubleType()),
        StructField("voltage", DoubleType()),
        StructField("current", DoubleType()),
        StructField("quality_flag", StringType()),
        StructField("timestamp", StringType())
    ]),
    "traffic": StructType([
        StructField("date_key", IntegerType()),
        StructField("time_key", StringType()),
        StructField("zone_id", StringType()),
        StructField("device_id", StringType()),
        StructField("vehicle_count", IntegerType()),
        StructField("avg_speed_kmh", DoubleType()),
        StructField("timestamp", StringType())
    ]),
    "bus_gps": StructType([
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
    ]),
    "waste": StructType([
        StructField("date_key", IntegerType()),
        StructField("time_key", StringType()),
        StructField("zone_id", StringType()),
        StructField("building_id", StringType()),
        StructField("container_id", StringType()),
        StructField("fill_level_percent", IntegerType()),
        StructField("truck_id", StringType()),
        StructField("timestamp", StringType())
    ]),
    "emergency": StructType([
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
}


def load_data(topic):
    """Load data from HDFS or Kafka"""
    hdfs_path = f"{HDFS_NAMENODE}/smartcity/{topic}"
    
    try:
        df = spark.read.parquet(hdfs_path)
        count = df.count()
        if count > 0:
            logger.info(f"  ✓ {topic}: {count:,} records from HDFS")
            return df
    except:
        pass
    
    # Try Kafka
    try:
        kafka_df = spark.read \
            .format("kafka") \
            .option("kafka.bootstrap.servers", KAFKA_BROKER) \
            .option("subscribe", topic) \
            .option("startingOffsets", "earliest") \
            .option("endingOffsets", "latest") \
            .load()
        
        df = kafka_df.select(
            from_json(col("value").cast("string"), schemas[topic]).alias("data")
        ).select("data.*")
        
        count = df.count()
        if count > 0:
            logger.info(f"  ✓ {topic}: {count:,} records from Kafka")
            return df
    except Exception as e:
        logger.warning(f"  ✗ {topic}: Failed to load - {e}")
    
    return None


def train_energy_model(df):
    """Train energy prediction model"""
    logger.info("\n" + "=" * 60)
    logger.info("🔌 ENERGY CONSUMPTION MODEL")
    logger.info("=" * 60)
    
    # Feature engineering
    features_df = df \
        .withColumn("hour", substring(col("time_key"), 1, 2).cast("int")) \
        .withColumn("day_of_week", dayofweek(to_date(col("date_key").cast("string"), "yyyyMMdd"))) \
        .withColumn("is_peak_hour", when((col("hour") >= 8) & (col("hour") <= 18), 1).otherwise(0)) \
        .withColumn("is_weekend", when((col("day_of_week") == 1) | (col("day_of_week") == 7), 1).otherwise(0)) \
        .filter(col("quality_flag") == "GOOD")
    
    if features_df.count() == 0:
        logger.warning("No valid energy data")
        return None
    
    # Pipeline
    building_idx = StringIndexer(inputCol="building_id", outputCol="building_idx", handleInvalid="keep")
    device_idx = StringIndexer(inputCol="device_id", outputCol="device_idx", handleInvalid="keep")
    
    assembler = VectorAssembler(
        inputCols=["building_idx", "device_idx", "hour", "day_of_week", "is_peak_hour", "is_weekend", "voltage", "current"],
        outputCol="features",
        handleInvalid="skip"
    )
    
    rf = RandomForestRegressor(featuresCol="features", labelCol="kwh", numTrees=50, maxDepth=8, seed=42)
    pipeline = Pipeline(stages=[building_idx, device_idx, assembler, rf])
    
    train, test = features_df.randomSplit([0.8, 0.2], seed=42)
    model = pipeline.fit(train)
    predictions = model.transform(test)
    
    rmse = RegressionEvaluator(labelCol="kwh", predictionCol="prediction", metricName="rmse").evaluate(predictions)
    r2 = RegressionEvaluator(labelCol="kwh", predictionCol="prediction", metricName="r2").evaluate(predictions)
    
    logger.info(f"  R² Score: {r2:.4f}")
    logger.info(f"  RMSE: {rmse:.4f} kWh")
    
    model.write().overwrite().save(f"{MODEL_BASE_PATH}/energy")
    logger.info("  ✓ Model saved")
    
    return {"r2": r2, "rmse": rmse}


def train_traffic_model(df):
    """Train traffic prediction model"""
    logger.info("\n" + "=" * 60)
    logger.info("🚗 TRAFFIC CONGESTION MODEL")
    logger.info("=" * 60)
    
    features_df = df \
        .withColumn("hour", substring(col("time_key"), 1, 2).cast("int")) \
        .withColumn("day_of_week", dayofweek(to_date(col("date_key").cast("string"), "yyyyMMdd"))) \
        .withColumn("is_rush_hour", 
            when(((col("hour") >= 7) & (col("hour") <= 9)) | 
                 ((col("hour") >= 17) & (col("hour") <= 19)), 1).otherwise(0)) \
        .filter(col("vehicle_count").isNotNull())
    
    if features_df.count() == 0:
        logger.warning("No valid traffic data")
        return None
    
    zone_idx = StringIndexer(inputCol="zone_id", outputCol="zone_idx", handleInvalid="keep")
    device_idx = StringIndexer(inputCol="device_id", outputCol="device_idx", handleInvalid="keep")
    
    assembler = VectorAssembler(
        inputCols=["zone_idx", "device_idx", "hour", "day_of_week", "is_rush_hour"],
        outputCol="features",
        handleInvalid="skip"
    )
    
    gbt = GBTRegressor(featuresCol="features", labelCol="vehicle_count", maxIter=30, maxDepth=6, seed=42)
    pipeline = Pipeline(stages=[zone_idx, device_idx, assembler, gbt])
    
    train, test = features_df.randomSplit([0.8, 0.2], seed=42)
    model = pipeline.fit(train)
    predictions = model.transform(test)
    
    rmse = RegressionEvaluator(labelCol="vehicle_count", predictionCol="prediction", metricName="rmse").evaluate(predictions)
    r2 = RegressionEvaluator(labelCol="vehicle_count", predictionCol="prediction", metricName="r2").evaluate(predictions)
    
    logger.info(f"  R² Score: {r2:.4f}")
    logger.info(f"  RMSE: {rmse:.4f} vehicles")
    
    model.write().overwrite().save(f"{MODEL_BASE_PATH}/traffic")
    logger.info("  ✓ Model saved")
    
    return {"r2": r2, "rmse": rmse}


def train_bus_model(df):
    """Train bus occupancy model"""
    logger.info("\n" + "=" * 60)
    logger.info("🚌 BUS OCCUPANCY MODEL")
    logger.info("=" * 60)
    
    features_df = df \
        .withColumn("hour", substring(col("time_key"), 1, 2).cast("int")) \
        .withColumn("day_of_week", dayofweek(to_date(col("date_key").cast("string"), "yyyyMMdd"))) \
        .withColumn("is_rush_hour", 
            when(((col("hour") >= 7) & (col("hour") <= 9)) | 
                 ((col("hour") >= 17) & (col("hour") <= 19)), 1).otherwise(0)) \
        .filter(col("occupancy_est").isNotNull())
    
    if features_df.count() == 0:
        logger.warning("No valid bus data")
        return None
    
    bus_idx = StringIndexer(inputCol="bus_id", outputCol="bus_idx", handleInvalid="keep")
    route_idx = StringIndexer(inputCol="route_id", outputCol="route_idx", handleInvalid="keep")
    zone_idx = StringIndexer(inputCol="zone_id", outputCol="zone_idx", handleInvalid="keep")
    
    assembler = VectorAssembler(
        inputCols=["bus_idx", "route_idx", "zone_idx", "hour", "day_of_week", "is_rush_hour", "speed_kmh"],
        outputCol="features",
        handleInvalid="skip"
    )
    
    rf = RandomForestRegressor(featuresCol="features", labelCol="occupancy_est", numTrees=50, maxDepth=8, seed=42)
    pipeline = Pipeline(stages=[bus_idx, route_idx, zone_idx, assembler, rf])
    
    train, test = features_df.randomSplit([0.8, 0.2], seed=42)
    model = pipeline.fit(train)
    predictions = model.transform(test)
    
    rmse = RegressionEvaluator(labelCol="occupancy_est", predictionCol="prediction", metricName="rmse").evaluate(predictions)
    r2 = RegressionEvaluator(labelCol="occupancy_est", predictionCol="prediction", metricName="r2").evaluate(predictions)
    
    logger.info(f"  R² Score: {r2:.4f}")
    logger.info(f"  RMSE: {rmse:.4f} passengers")
    
    model.write().overwrite().save(f"{MODEL_BASE_PATH}/bus")
    logger.info("  ✓ Model saved")
    
    return {"r2": r2, "rmse": rmse}


def train_waste_model(df):
    """Train waste fill level model"""
    logger.info("\n" + "=" * 60)
    logger.info("🗑️  WASTE COLLECTION MODEL")
    logger.info("=" * 60)
    
    features_df = df \
        .withColumn("hour", substring(col("time_key"), 1, 2).cast("int")) \
        .withColumn("day_of_week", dayofweek(to_date(col("date_key").cast("string"), "yyyyMMdd"))) \
        .withColumn("is_weekend", when((col("day_of_week") == 1) | (col("day_of_week") == 7), 1).otherwise(0)) \
        .filter(col("fill_level_percent").isNotNull())
    
    if features_df.count() == 0:
        logger.warning("No valid waste data")
        return None
    
    zone_idx = StringIndexer(inputCol="zone_id", outputCol="zone_idx", handleInvalid="keep")
    building_idx = StringIndexer(inputCol="building_id", outputCol="building_idx", handleInvalid="keep")
    container_idx = StringIndexer(inputCol="container_id", outputCol="container_idx", handleInvalid="keep")
    
    assembler = VectorAssembler(
        inputCols=["zone_idx", "building_idx", "container_idx", "hour", "day_of_week", "is_weekend"],
        outputCol="features",
        handleInvalid="skip"
    )
    
    rf = RandomForestRegressor(featuresCol="features", labelCol="fill_level_percent", numTrees=50, maxDepth=8, seed=42)
    pipeline = Pipeline(stages=[zone_idx, building_idx, container_idx, assembler, rf])
    
    train, test = features_df.randomSplit([0.8, 0.2], seed=42)
    model = pipeline.fit(train)
    predictions = model.transform(test)
    
    rmse = RegressionEvaluator(labelCol="fill_level_percent", predictionCol="prediction", metricName="rmse").evaluate(predictions)
    r2 = RegressionEvaluator(labelCol="fill_level_percent", predictionCol="prediction", metricName="r2").evaluate(predictions)
    
    logger.info(f"  R² Score: {r2:.4f}")
    logger.info(f"  RMSE: {rmse:.4f}%")
    
    model.write().overwrite().save(f"{MODEL_BASE_PATH}/waste")
    logger.info("  ✓ Model saved")
    
    return {"r2": r2, "rmse": rmse}


def train_emergency_model(df):
    """Train emergency response model"""
    logger.info("\n" + "=" * 60)
    logger.info("🚨 EMERGENCY RESPONSE MODEL")
    logger.info("=" * 60)
    
    features_df = df \
        .withColumn("hour", substring(col("time_key"), 1, 2).cast("int")) \
        .withColumn("day_of_week", dayofweek(to_date(col("date_key").cast("string"), "yyyyMMdd"))) \
        .withColumn("is_night", when((col("hour") >= 22) | (col("hour") <= 5), 1).otherwise(0)) \
        .withColumn("priority_numeric",
            when(col("priority_level") == "Critical", 4)
            .when(col("priority_level") == "High", 3)
            .when(col("priority_level") == "Medium", 2)
            .otherwise(1)) \
        .filter(col("response_time_minutes").isNotNull())
    
    if features_df.count() == 0:
        logger.warning("No valid emergency data")
        return None
    
    zone_idx = StringIndexer(inputCol="zone_id", outputCol="zone_idx", handleInvalid="keep")
    event_idx = StringIndexer(inputCol="event_type_id", outputCol="event_idx", handleInvalid="keep")
    
    assembler = VectorAssembler(
        inputCols=["zone_idx", "event_idx", "hour", "day_of_week", "is_night", "priority_numeric"],
        outputCol="features",
        handleInvalid="skip"
    )
    
    gbt = GBTRegressor(featuresCol="features", labelCol="response_time_minutes", maxIter=30, maxDepth=6, seed=42)
    pipeline = Pipeline(stages=[zone_idx, event_idx, assembler, gbt])
    
    train, test = features_df.randomSplit([0.8, 0.2], seed=42)
    model = pipeline.fit(train)
    predictions = model.transform(test)
    
    rmse = RegressionEvaluator(labelCol="response_time_minutes", predictionCol="prediction", metricName="rmse").evaluate(predictions)
    r2 = RegressionEvaluator(labelCol="response_time_minutes", predictionCol="prediction", metricName="r2").evaluate(predictions)
    
    logger.info(f"  R² Score: {r2:.4f}")
    logger.info(f"  RMSE: {rmse:.4f} minutes")
    
    model.write().overwrite().save(f"{MODEL_BASE_PATH}/emergency")
    logger.info("  ✓ Model saved")
    
    return {"r2": r2, "rmse": rmse}


# Main execution
try:
    logger.info("Loading data from all sources...")
    
    data = {}
    for topic in ["energy", "traffic", "bus_gps", "waste", "emergency"]:
        data[topic] = load_data(topic)
    
    logger.info("")
    
    # Check if we have data
    valid_data = {k: v for k, v in data.items() if v is not None and v.count() > 0}
    
    if not valid_data:
        logger.error("No data available! Run the data producer first.")
        spark.stop()
        sys.exit(1)
    
    # Train models
    results = {}
    
    if "energy" in valid_data:
        results["energy"] = train_energy_model(valid_data["energy"])
    
    if "traffic" in valid_data:
        results["traffic"] = train_traffic_model(valid_data["traffic"])
    
    if "bus_gps" in valid_data:
        results["bus"] = train_bus_model(valid_data["bus_gps"])
    
    if "waste" in valid_data:
        results["waste"] = train_waste_model(valid_data["waste"])
    
    if "emergency" in valid_data:
        results["emergency"] = train_emergency_model(valid_data["emergency"])
    
    # Summary
    logger.info("")
    logger.info("=" * 80)
    logger.info("📊 MODEL TRAINING SUMMARY")
    logger.info("=" * 80)
    
    for name, metrics in results.items():
        if metrics:
            logger.info(f"  {name.upper():12s} - R²: {metrics['r2']:.4f}, RMSE: {metrics['rmse']:.4f}")
        else:
            logger.info(f"  {name.upper():12s} - ⚠️  No data available")
    
    logger.info("")
    logger.info(f"Models saved to: {MODEL_BASE_PATH}/")
    logger.info("=" * 80)
    logger.info("")
    logger.info("🏙️  Smart City ML Pipeline Complete!")
    logger.info("")

except Exception as e:
    logger.error(f"Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    spark.stop()
