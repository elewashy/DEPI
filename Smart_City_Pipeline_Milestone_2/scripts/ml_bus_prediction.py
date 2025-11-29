#!/usr/bin/env python3
"""
Smart City ML - Bus Occupancy and Delay Prediction
Predicts bus occupancy levels and potential delays
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
from pyspark.ml.feature import VectorAssembler, StringIndexer, StandardScaler
from pyspark.ml.regression import RandomForestRegressor
from pyspark.ml.classification import GBTClassifier
from pyspark.ml.evaluation import RegressionEvaluator, BinaryClassificationEvaluator
from pyspark.ml import Pipeline
import logging
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
KAFKA_BROKER = "kafka:9092"
HDFS_NAMENODE = "hdfs://namenode:9000"
MODEL_PATH = "/tmp/models/bus_prediction"

# Create Spark session
spark = SparkSession.builder \
    .appName("SmartCityBusML") \
    .config("spark.sql.shuffle.partitions", "4") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")

logger.info("=" * 80)
logger.info("🚌 Smart City ML - Bus Occupancy & Delay Prediction")
logger.info("=" * 80)
logger.info("")

# Schema
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


def load_data():
    """Load bus GPS data"""
    hdfs_path = f"{HDFS_NAMENODE}/smartcity/bus_gps"
    
    try:
        df = spark.read.parquet(hdfs_path)
        logger.info(f"✓ Loaded {df.count():,} records from HDFS")
        return df
    except Exception as e:
        logger.warning(f"HDFS not available: {e}")
        logger.info("Loading from Kafka...")
        
        kafka_df = spark.read \
            .format("kafka") \
            .option("kafka.bootstrap.servers", KAFKA_BROKER) \
            .option("subscribe", "bus_gps") \
            .option("startingOffsets", "earliest") \
            .option("endingOffsets", "latest") \
            .load()
        
        df = kafka_df.select(
            from_json(col("value").cast("string"), bus_gps_schema).alias("data")
        ).select("data.*")
        
        logger.info(f"✓ Loaded {df.count():,} records from Kafka")
        return df


def engineer_features(df):
    """Create ML features for bus prediction"""
    logger.info("Engineering features...")
    
    features_df = df \
        .withColumn("hour", substring(col("time_key"), 1, 2).cast("int")) \
        .withColumn("minute", substring(col("time_key"), 3, 2).cast("int")) \
        .withColumn("day_of_week", 
            dayofweek(to_date(col("date_key").cast("string"), "yyyyMMdd"))) \
        .withColumn("is_rush_hour", 
            when(((col("hour") >= 7) & (col("hour") <= 9)) | 
                 ((col("hour") >= 17) & (col("hour") <= 19)), 1).otherwise(0)) \
        .withColumn("is_weekend", 
            when((col("day_of_week") == 1) | (col("day_of_week") == 7), 1).otherwise(0)) \
        .withColumn("time_period",
            when(col("hour") < 6, 0)  # Early morning
            .when(col("hour") < 10, 1)  # Morning rush
            .when(col("hour") < 16, 2)  # Midday
            .when(col("hour") < 20, 3)  # Evening rush
            .otherwise(4)) \
        .withColumn("is_delayed", 
            when(col("speed_kmh") < 15, 1).otherwise(0)) \
        .withColumn("occupancy_level",
            when(col("occupancy_est") > 80, 2)  # Full
            .when(col("occupancy_est") > 50, 1)  # Crowded
            .otherwise(0)) \
        .filter(col("occupancy_est").isNotNull())
    
    return features_df


def train_occupancy_model(df):
    """Train model to predict bus occupancy"""
    logger.info("")
    logger.info("=" * 60)
    logger.info("OCCUPANCY PREDICTION (Regression)")
    logger.info("=" * 60)
    
    # Indexers
    bus_indexer = StringIndexer(inputCol="bus_id", outputCol="bus_idx", handleInvalid="keep")
    route_indexer = StringIndexer(inputCol="route_id", outputCol="route_idx", handleInvalid="keep")
    zone_indexer = StringIndexer(inputCol="zone_id", outputCol="zone_idx", handleInvalid="keep")
    
    feature_cols = [
        "bus_idx", "route_idx", "zone_idx", "hour", "minute",
        "day_of_week", "is_rush_hour", "is_weekend", "time_period", "speed_kmh"
    ]
    
    assembler = VectorAssembler(inputCols=feature_cols, outputCol="features_raw", handleInvalid="skip")
    scaler = StandardScaler(inputCol="features_raw", outputCol="features", withStd=True, withMean=False)
    
    rf = RandomForestRegressor(
        featuresCol="features",
        labelCol="occupancy_est",
        numTrees=100,
        maxDepth=12,
        seed=42
    )
    
    pipeline = Pipeline(stages=[bus_indexer, route_indexer, zone_indexer, assembler, scaler, rf])
    
    train_data, test_data = df.randomSplit([0.8, 0.2], seed=42)
    
    logger.info(f"Training: {train_data.count():,}, Testing: {test_data.count():,}")
    logger.info("Training Random Forest Regressor...")
    
    model = pipeline.fit(train_data)
    predictions = model.transform(test_data)
    
    # Evaluate
    rmse = RegressionEvaluator(labelCol="occupancy_est", predictionCol="prediction", metricName="rmse").evaluate(predictions)
    r2 = RegressionEvaluator(labelCol="occupancy_est", predictionCol="prediction", metricName="r2").evaluate(predictions)
    mae = RegressionEvaluator(labelCol="occupancy_est", predictionCol="prediction", metricName="mae").evaluate(predictions)
    
    logger.info("")
    logger.info(f"R² Score:  {r2:.4f}")
    logger.info(f"RMSE:      {rmse:.4f} passengers")
    logger.info(f"MAE:       {mae:.4f} passengers")
    
    # Feature importance
    rf_model = model.stages[-1]
    importance = rf_model.featureImportances.toArray()
    
    logger.info("")
    logger.info("Top Features:")
    for i, col_name in enumerate(feature_cols[:5]):
        logger.info(f"  {col_name:15s}: {importance[i]:.4f}")
    
    # Sample predictions
    logger.info("")
    logger.info("Sample Predictions:")
    predictions.select("bus_id", "route_id", "hour", "occupancy_est", "prediction") \
        .withColumn("prediction", round(col("prediction"), 0)) \
        .show(10, truncate=False)
    
    return model


def train_delay_model(df):
    """Train model to predict bus delays"""
    logger.info("")
    logger.info("=" * 60)
    logger.info("DELAY PREDICTION (Classification)")
    logger.info("=" * 60)
    
    # Indexers
    bus_indexer = StringIndexer(inputCol="bus_id", outputCol="bus_idx", handleInvalid="keep")
    route_indexer = StringIndexer(inputCol="route_id", outputCol="route_idx", handleInvalid="keep")
    zone_indexer = StringIndexer(inputCol="zone_id", outputCol="zone_idx", handleInvalid="keep")
    
    feature_cols = [
        "bus_idx", "route_idx", "zone_idx", "hour",
        "day_of_week", "is_rush_hour", "is_weekend", "occupancy_est"
    ]
    
    assembler = VectorAssembler(inputCols=feature_cols, outputCol="features", handleInvalid="skip")
    
    gbt = GBTClassifier(
        featuresCol="features",
        labelCol="is_delayed",
        maxIter=50,
        maxDepth=8,
        seed=42
    )
    
    pipeline = Pipeline(stages=[bus_indexer, route_indexer, zone_indexer, assembler, gbt])
    
    train_data, test_data = df.randomSplit([0.8, 0.2], seed=42)
    
    logger.info(f"Training: {train_data.count():,}, Testing: {test_data.count():,}")
    logger.info("Training GBT Classifier...")
    
    model = pipeline.fit(train_data)
    predictions = model.transform(test_data)
    
    # Evaluate
    auc = BinaryClassificationEvaluator(
        labelCol="is_delayed", 
        rawPredictionCol="rawPrediction", 
        metricName="areaUnderROC"
    ).evaluate(predictions)
    
    logger.info("")
    logger.info(f"AUC-ROC: {auc:.4f}")
    
    # Calculate accuracy manually
    correct = predictions.filter(col("is_delayed") == col("prediction")).count()
    total = predictions.count()
    accuracy = correct / total if total > 0 else 0
    
    logger.info(f"Accuracy: {accuracy:.4f}")
    
    # Delay analysis
    logger.info("")
    logger.info("Delay Predictions by Route:")
    predictions.groupBy("route_id") \
        .agg(
            sum("is_delayed").alias("actual_delays"),
            sum("prediction").alias("predicted_delays"),
            count("*").alias("total")
        ) \
        .withColumn("actual_rate", round(col("actual_delays") / col("total") * 100, 1)) \
        .withColumn("predicted_rate", round(col("predicted_delays") / col("total") * 100, 1)) \
        .orderBy(desc("actual_delays")) \
        .show(10, truncate=False)
    
    return model


def analyze_patterns(df):
    """Analyze bus patterns"""
    logger.info("")
    logger.info("=" * 60)
    logger.info("BUS SERVICE PATTERNS")
    logger.info("=" * 60)
    
    # By route
    logger.info("\nAverage Metrics by Route:")
    df.groupBy("route_id") \
        .agg(
            avg("occupancy_est").alias("avg_occupancy"),
            avg("speed_kmh").alias("avg_speed"),
            sum("is_delayed").alias("total_delays"),
            count("*").alias("readings")
        ) \
        .orderBy(desc("avg_occupancy")) \
        .show(10, truncate=False)
    
    # By time period
    logger.info("\nOccupancy by Time Period:")
    df.groupBy("time_period") \
        .agg(
            avg("occupancy_est").alias("avg_occupancy"),
            avg("speed_kmh").alias("avg_speed")
        ) \
        .orderBy("time_period") \
        .show()
    
    # High occupancy analysis
    logger.info("\nHigh Occupancy Buses (>80%):")
    df.filter(col("occupancy_est") > 80) \
        .groupBy("route_id", "hour") \
        .count() \
        .orderBy(desc("count")) \
        .show(10)


# Main execution
try:
    raw_data = load_data()
    
    if raw_data.count() == 0:
        logger.error("No data available!")
        spark.stop()
        sys.exit(1)
    
    features_df = engineer_features(raw_data)
    
    if features_df.count() == 0:
        logger.error("No valid data after processing!")
        spark.stop()
        sys.exit(1)
    
    logger.info(f"Total records: {features_df.count():,}")
    
    # Statistics
    logger.info("\nBus GPS Statistics:")
    features_df.select(
        avg("occupancy_est").alias("avg_occupancy"),
        avg("speed_kmh").alias("avg_speed"),
        sum("is_delayed").alias("total_delays")
    ).show()
    
    # Train models
    occupancy_model = train_occupancy_model(features_df)
    delay_model = train_delay_model(features_df)
    
    # Analyze patterns
    analyze_patterns(features_df)
    
    # Save models
    logger.info(f"\nSaving models to {MODEL_PATH}...")
    occupancy_model.write().overwrite().save(f"{MODEL_PATH}_occupancy")
    delay_model.write().overwrite().save(f"{MODEL_PATH}_delay")
    logger.info("✓ Models saved!")
    
    logger.info("")
    logger.info("=" * 80)
    logger.info("🚌 Bus Prediction Model Training Complete!")
    logger.info("=" * 80)
    logger.info("")
    logger.info("Use cases:")
    logger.info("  • Predict bus crowding")
    logger.info("  • Anticipate delays")
    logger.info("  • Optimize bus frequency")
    logger.info("  • Passenger information systems")
    logger.info("")

except Exception as e:
    logger.error(f"Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    spark.stop()
