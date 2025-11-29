#!/usr/bin/env python3
"""
Smart City ML - Traffic Congestion Prediction
Predicts vehicle counts and congestion levels by zone and time
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
from pyspark.ml.feature import VectorAssembler, StringIndexer, StandardScaler
from pyspark.ml.regression import GBTRegressor
from pyspark.ml.classification import RandomForestClassifier
from pyspark.ml.evaluation import RegressionEvaluator, MulticlassClassificationEvaluator
from pyspark.ml import Pipeline
import logging
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
KAFKA_BROKER = "kafka:9092"
HDFS_NAMENODE = "hdfs://namenode:9000"
MODEL_PATH = "/tmp/models/traffic_prediction"

# Create Spark session
spark = SparkSession.builder \
    .appName("SmartCityTrafficML") \
    .config("spark.sql.shuffle.partitions", "4") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")

logger.info("=" * 80)
logger.info("🚗 Smart City ML - Traffic Congestion Prediction")
logger.info("=" * 80)
logger.info("")

# Schema
traffic_schema = StructType([
    StructField("date_key", IntegerType()),
    StructField("time_key", StringType()),
    StructField("zone_id", StringType()),
    StructField("device_id", StringType()),
    StructField("vehicle_count", IntegerType()),
    StructField("avg_speed_kmh", DoubleType()),
    StructField("timestamp", StringType())
])


def load_data():
    """Load traffic data from HDFS or Kafka"""
    hdfs_path = f"{HDFS_NAMENODE}/smartcity/traffic"
    
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
            .option("subscribe", "traffic") \
            .option("startingOffsets", "earliest") \
            .option("endingOffsets", "latest") \
            .load()
        
        df = kafka_df.select(
            from_json(col("value").cast("string"), traffic_schema).alias("data")
        ).select("data.*")
        
        logger.info(f"✓ Loaded {df.count():,} records from Kafka")
        return df


def engineer_features(df):
    """Create ML features for traffic prediction"""
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
        .withColumn("is_night", 
            when((col("hour") >= 22) | (col("hour") <= 5), 1).otherwise(0)) \
        .withColumn("time_of_day",
            when(col("hour") < 6, 0)  # Night
            .when(col("hour") < 12, 1)  # Morning
            .when(col("hour") < 18, 2)  # Afternoon
            .otherwise(3)) \
        .withColumn("congestion_label",
            when(col("vehicle_count") > 100, 2)  # Heavy
            .when(col("vehicle_count") > 60, 1)  # Moderate
            .otherwise(0)) \
        .filter(col("vehicle_count").isNotNull())
    
    return features_df


def train_regression_model(df):
    """Train model to predict vehicle count"""
    logger.info("")
    logger.info("=" * 60)
    logger.info("VEHICLE COUNT PREDICTION (Regression)")
    logger.info("=" * 60)
    
    # Indexers
    zone_indexer = StringIndexer(inputCol="zone_id", outputCol="zone_idx", handleInvalid="keep")
    device_indexer = StringIndexer(inputCol="device_id", outputCol="device_idx", handleInvalid="keep")
    
    feature_cols = [
        "zone_idx", "device_idx", "hour", "minute", "day_of_week",
        "is_rush_hour", "is_weekend", "is_night", "time_of_day"
    ]
    
    assembler = VectorAssembler(inputCols=feature_cols, outputCol="features_raw", handleInvalid="skip")
    scaler = StandardScaler(inputCol="features_raw", outputCol="features", withStd=True, withMean=False)
    
    # GBT Regressor for vehicle count
    gbt = GBTRegressor(
        featuresCol="features",
        labelCol="vehicle_count",
        maxIter=50,
        maxDepth=8,
        seed=42
    )
    
    pipeline = Pipeline(stages=[zone_indexer, device_indexer, assembler, scaler, gbt])
    
    train_data, test_data = df.randomSplit([0.8, 0.2], seed=42)
    
    logger.info(f"Training: {train_data.count():,}, Testing: {test_data.count():,}")
    logger.info("Training GBT Regressor...")
    
    model = pipeline.fit(train_data)
    predictions = model.transform(test_data)
    
    # Evaluate
    rmse = RegressionEvaluator(labelCol="vehicle_count", predictionCol="prediction", metricName="rmse").evaluate(predictions)
    r2 = RegressionEvaluator(labelCol="vehicle_count", predictionCol="prediction", metricName="r2").evaluate(predictions)
    mae = RegressionEvaluator(labelCol="vehicle_count", predictionCol="prediction", metricName="mae").evaluate(predictions)
    
    logger.info("")
    logger.info(f"R² Score:  {r2:.4f}")
    logger.info(f"RMSE:      {rmse:.4f} vehicles")
    logger.info(f"MAE:       {mae:.4f} vehicles")
    
    # Sample predictions
    logger.info("")
    logger.info("Sample Predictions:")
    predictions.select("zone_id", "hour", "is_rush_hour", "vehicle_count", "prediction") \
        .withColumn("prediction", round(col("prediction"), 1)) \
        .show(10, truncate=False)
    
    return model


def train_classification_model(df):
    """Train model to classify congestion level"""
    logger.info("")
    logger.info("=" * 60)
    logger.info("CONGESTION LEVEL CLASSIFICATION")
    logger.info("=" * 60)
    
    # Indexers
    zone_indexer = StringIndexer(inputCol="zone_id", outputCol="zone_idx", handleInvalid="keep")
    device_indexer = StringIndexer(inputCol="device_id", outputCol="device_idx", handleInvalid="keep")
    
    feature_cols = [
        "zone_idx", "device_idx", "hour", "day_of_week",
        "is_rush_hour", "is_weekend", "is_night", "avg_speed_kmh"
    ]
    
    assembler = VectorAssembler(inputCols=feature_cols, outputCol="features", handleInvalid="skip")
    
    # Random Forest Classifier
    rf = RandomForestClassifier(
        featuresCol="features",
        labelCol="congestion_label",
        numTrees=100,
        maxDepth=10,
        seed=42
    )
    
    pipeline = Pipeline(stages=[zone_indexer, device_indexer, assembler, rf])
    
    train_data, test_data = df.randomSplit([0.8, 0.2], seed=42)
    
    logger.info(f"Training: {train_data.count():,}, Testing: {test_data.count():,}")
    logger.info("Training Random Forest Classifier...")
    
    model = pipeline.fit(train_data)
    predictions = model.transform(test_data)
    
    # Evaluate
    accuracy = MulticlassClassificationEvaluator(
        labelCol="congestion_label", 
        predictionCol="prediction", 
        metricName="accuracy"
    ).evaluate(predictions)
    
    f1 = MulticlassClassificationEvaluator(
        labelCol="congestion_label", 
        predictionCol="prediction", 
        metricName="f1"
    ).evaluate(predictions)
    
    logger.info("")
    logger.info(f"Accuracy: {accuracy:.4f}")
    logger.info(f"F1 Score: {f1:.4f}")
    
    # Confusion matrix style analysis
    logger.info("")
    logger.info("Classification Results by Zone:")
    predictions.groupBy("zone_id", "congestion_label", "prediction") \
        .count() \
        .orderBy("zone_id", "congestion_label") \
        .show(20, truncate=False)
    
    return model


def analyze_patterns(df):
    """Analyze traffic patterns"""
    logger.info("")
    logger.info("=" * 60)
    logger.info("TRAFFIC PATTERNS ANALYSIS")
    logger.info("=" * 60)
    
    # By zone
    logger.info("\nAverage Traffic by Zone:")
    df.groupBy("zone_id") \
        .agg(
            avg("vehicle_count").alias("avg_vehicles"),
            avg("avg_speed_kmh").alias("avg_speed"),
            count("*").alias("readings")
        ) \
        .orderBy(desc("avg_vehicles")) \
        .show(10, truncate=False)
    
    # By hour
    logger.info("\nAverage Traffic by Hour:")
    df.groupBy("hour") \
        .agg(
            avg("vehicle_count").alias("avg_vehicles"),
            avg("avg_speed_kmh").alias("avg_speed")
        ) \
        .orderBy("hour") \
        .show(24, truncate=False)
    
    # Rush hour analysis
    logger.info("\nRush Hour vs Non-Rush Hour:")
    df.groupBy("is_rush_hour") \
        .agg(
            avg("vehicle_count").alias("avg_vehicles"),
            avg("avg_speed_kmh").alias("avg_speed"),
            count("*").alias("readings")
        ) \
        .show()


# Main execution
try:
    raw_data = load_data()
    
    if raw_data.count() == 0:
        logger.error("No data available! Run the data producer first.")
        spark.stop()
        sys.exit(1)
    
    features_df = engineer_features(raw_data)
    
    if features_df.count() == 0:
        logger.error("No valid data after processing!")
        spark.stop()
        sys.exit(1)
    
    logger.info(f"Total records: {features_df.count():,}")
    
    # Statistics
    logger.info("\nTraffic Statistics:")
    features_df.select(
        avg("vehicle_count").alias("avg_vehicles"),
        min("vehicle_count").alias("min_vehicles"),
        max("vehicle_count").alias("max_vehicles"),
        avg("avg_speed_kmh").alias("avg_speed")
    ).show()
    
    # Train models
    reg_model = train_regression_model(features_df)
    clf_model = train_classification_model(features_df)
    
    # Analyze patterns
    analyze_patterns(features_df)
    
    # Save models
    logger.info(f"\nSaving models to {MODEL_PATH}...")
    reg_model.write().overwrite().save(f"{MODEL_PATH}_regression")
    clf_model.write().overwrite().save(f"{MODEL_PATH}_classification")
    logger.info("✓ Models saved!")
    
    logger.info("")
    logger.info("=" * 80)
    logger.info("🚗 Traffic Prediction Model Training Complete!")
    logger.info("=" * 80)
    logger.info("")
    logger.info("Use cases:")
    logger.info("  • Predict traffic congestion")
    logger.info("  • Optimize traffic signal timing")
    logger.info("  • Route recommendation")
    logger.info("  • City planning insights")
    logger.info("")

except Exception as e:
    logger.error(f"Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    spark.stop()
