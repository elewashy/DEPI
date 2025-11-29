#!/usr/bin/env python3
"""
Smart City ML - Emergency Response Prediction
Predicts response times and emergency patterns
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
from pyspark.ml.feature import VectorAssembler, StringIndexer, StandardScaler, OneHotEncoder
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
MODEL_PATH = "/tmp/models/emergency_prediction"

# Create Spark session
spark = SparkSession.builder \
    .appName("SmartCityEmergencyML") \
    .config("spark.sql.shuffle.partitions", "4") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")

logger.info("=" * 80)
logger.info("🚨 Smart City ML - Emergency Response Prediction")
logger.info("=" * 80)
logger.info("")

# Schema
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


def load_data():
    """Load emergency data"""
    hdfs_path = f"{HDFS_NAMENODE}/smartcity/emergency"
    
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
            .option("subscribe", "emergency") \
            .option("startingOffsets", "earliest") \
            .option("endingOffsets", "latest") \
            .load()
        
        df = kafka_df.select(
            from_json(col("value").cast("string"), emergency_schema).alias("data")
        ).select("data.*")
        
        logger.info(f"✓ Loaded {df.count():,} records from Kafka")
        return df


def engineer_features(df):
    """Create ML features for emergency prediction"""
    logger.info("Engineering features...")
    
    features_df = df \
        .withColumn("hour", substring(col("time_key"), 1, 2).cast("int")) \
        .withColumn("day_of_week", 
            dayofweek(to_date(col("date_key").cast("string"), "yyyyMMdd"))) \
        .withColumn("is_weekend", 
            when((col("day_of_week") == 1) | (col("day_of_week") == 7), 1).otherwise(0)) \
        .withColumn("is_night", 
            when((col("hour") >= 22) | (col("hour") <= 5), 1).otherwise(0)) \
        .withColumn("time_period",
            when(col("hour") < 6, 0)
            .when(col("hour") < 12, 1)
            .when(col("hour") < 18, 2)
            .otherwise(3)) \
        .withColumn("priority_numeric",
            when(col("priority_level") == "Critical", 4)
            .when(col("priority_level") == "High", 3)
            .when(col("priority_level") == "Medium", 2)
            .otherwise(1)) \
        .withColumn("response_category",
            when(col("response_time_minutes") <= 5, 0)  # Excellent
            .when(col("response_time_minutes") <= 15, 1)  # Good
            .when(col("response_time_minutes") <= 30, 2)  # Acceptable
            .otherwise(3)) \
        .withColumn("is_delayed", 
            when(col("response_time_minutes") > 20, 1).otherwise(0)) \
        .filter(col("response_time_minutes").isNotNull())
    
    return features_df


def train_response_time_model(df):
    """Train model to predict response times"""
    logger.info("")
    logger.info("=" * 60)
    logger.info("RESPONSE TIME PREDICTION (Regression)")
    logger.info("=" * 60)
    
    # Indexers
    zone_indexer = StringIndexer(inputCol="zone_id", outputCol="zone_idx", handleInvalid="keep")
    building_indexer = StringIndexer(inputCol="building_id", outputCol="building_idx", handleInvalid="keep")
    event_indexer = StringIndexer(inputCol="event_type_id", outputCol="event_idx", handleInvalid="keep")
    priority_indexer = StringIndexer(inputCol="priority_level", outputCol="priority_idx", handleInvalid="keep")
    
    feature_cols = [
        "zone_idx", "building_idx", "event_idx", "priority_idx",
        "hour", "day_of_week", "is_weekend", "is_night", "time_period", "priority_numeric"
    ]
    
    assembler = VectorAssembler(inputCols=feature_cols, outputCol="features_raw", handleInvalid="skip")
    scaler = StandardScaler(inputCol="features_raw", outputCol="features", withStd=True, withMean=False)
    
    gbt = GBTRegressor(
        featuresCol="features",
        labelCol="response_time_minutes",
        maxIter=50,
        maxDepth=8,
        seed=42
    )
    
    pipeline = Pipeline(stages=[
        zone_indexer, building_indexer, event_indexer, priority_indexer,
        assembler, scaler, gbt
    ])
    
    train_data, test_data = df.randomSplit([0.8, 0.2], seed=42)
    
    logger.info(f"Training: {train_data.count():,}, Testing: {test_data.count():,}")
    logger.info("Training GBT Regressor...")
    
    model = pipeline.fit(train_data)
    predictions = model.transform(test_data)
    
    # Evaluate
    rmse = RegressionEvaluator(labelCol="response_time_minutes", predictionCol="prediction", metricName="rmse").evaluate(predictions)
    r2 = RegressionEvaluator(labelCol="response_time_minutes", predictionCol="prediction", metricName="r2").evaluate(predictions)
    mae = RegressionEvaluator(labelCol="response_time_minutes", predictionCol="prediction", metricName="mae").evaluate(predictions)
    
    logger.info("")
    logger.info(f"R² Score:  {r2:.4f}")
    logger.info(f"RMSE:      {rmse:.4f} minutes")
    logger.info(f"MAE:       {mae:.4f} minutes")
    
    # Sample predictions
    logger.info("")
    logger.info("Sample Predictions:")
    predictions.select(
        "zone_id", "event_type_id", "priority_level", 
        "response_time_minutes", "prediction"
    ).withColumn("prediction", round(col("prediction"), 1)) \
     .show(10, truncate=False)
    
    return model


def train_priority_classifier(df):
    """Train model to classify emergency priority"""
    logger.info("")
    logger.info("=" * 60)
    logger.info("RESPONSE QUALITY CLASSIFICATION")
    logger.info("=" * 60)
    
    # Indexers
    zone_indexer = StringIndexer(inputCol="zone_id", outputCol="zone_idx", handleInvalid="keep")
    event_indexer = StringIndexer(inputCol="event_type_id", outputCol="event_idx", handleInvalid="keep")
    priority_indexer = StringIndexer(inputCol="priority_level", outputCol="priority_idx", handleInvalid="keep")
    
    feature_cols = [
        "zone_idx", "event_idx", "priority_idx",
        "hour", "day_of_week", "is_weekend", "is_night", "priority_numeric"
    ]
    
    assembler = VectorAssembler(inputCols=feature_cols, outputCol="features", handleInvalid="skip")
    
    rf = RandomForestClassifier(
        featuresCol="features",
        labelCol="response_category",
        numTrees=100,
        maxDepth=10,
        seed=42
    )
    
    pipeline = Pipeline(stages=[zone_indexer, event_indexer, priority_indexer, assembler, rf])
    
    train_data, test_data = df.randomSplit([0.8, 0.2], seed=42)
    
    logger.info(f"Training: {train_data.count():,}, Testing: {test_data.count():,}")
    logger.info("Training Random Forest Classifier...")
    
    model = pipeline.fit(train_data)
    predictions = model.transform(test_data)
    
    # Evaluate
    accuracy = MulticlassClassificationEvaluator(
        labelCol="response_category", 
        predictionCol="prediction", 
        metricName="accuracy"
    ).evaluate(predictions)
    
    f1 = MulticlassClassificationEvaluator(
        labelCol="response_category", 
        predictionCol="prediction", 
        metricName="f1"
    ).evaluate(predictions)
    
    logger.info("")
    logger.info(f"Accuracy: {accuracy:.4f}")
    logger.info(f"F1 Score: {f1:.4f}")
    
    # Response categories: 0=Excellent, 1=Good, 2=Acceptable, 3=Delayed
    logger.info("")
    logger.info("Response Quality Distribution:")
    predictions.groupBy("response_category", "prediction") \
        .count() \
        .orderBy("response_category", "prediction") \
        .show(20)
    
    return model


def analyze_patterns(df):
    """Analyze emergency patterns"""
    logger.info("")
    logger.info("=" * 60)
    logger.info("EMERGENCY PATTERNS ANALYSIS")
    logger.info("=" * 60)
    
    # By event type
    logger.info("\nEmergencies by Type:")
    df.groupBy("event_type_id") \
        .agg(
            count("*").alias("total_calls"),
            avg("response_time_minutes").alias("avg_response"),
            sum("is_delayed").alias("delayed_count")
        ) \
        .withColumn("delay_rate", round(col("delayed_count") / col("total_calls") * 100, 1)) \
        .orderBy(desc("total_calls")) \
        .show(10, truncate=False)
    
    # By zone
    logger.info("\nEmergencies by Zone:")
    df.groupBy("zone_id") \
        .agg(
            count("*").alias("total_calls"),
            avg("response_time_minutes").alias("avg_response"),
            sum(when(col("priority_level") == "Critical", 1).otherwise(0)).alias("critical_count")
        ) \
        .orderBy(desc("total_calls")) \
        .show(10, truncate=False)
    
    # By priority
    logger.info("\nResponse Time by Priority:")
    df.groupBy("priority_level") \
        .agg(
            count("*").alias("count"),
            avg("response_time_minutes").alias("avg_response"),
            min("response_time_minutes").alias("min_response"),
            max("response_time_minutes").alias("max_response")
        ) \
        .orderBy(desc("count")) \
        .show()
    
    # Hot spots (zones with most critical emergencies)
    logger.info("\nEmergency Hotspots (Critical Priority):")
    df.filter(col("priority_level") == "Critical") \
        .groupBy("zone_id", "event_type_id") \
        .count() \
        .orderBy(desc("count")) \
        .show(10, truncate=False)
    
    # Time patterns
    logger.info("\nEmergencies by Hour:")
    df.groupBy("hour") \
        .agg(
            count("*").alias("count"),
            avg("response_time_minutes").alias("avg_response")
        ) \
        .orderBy("hour") \
        .show(24)


def generate_recommendations(df):
    """Generate actionable recommendations"""
    logger.info("")
    logger.info("=" * 60)
    logger.info("RECOMMENDATIONS")
    logger.info("=" * 60)
    
    # Zones needing more resources
    delayed_zones = df.filter(col("response_time_minutes") > 20) \
        .groupBy("zone_id") \
        .count() \
        .orderBy(desc("count")) \
        .limit(5) \
        .collect()
    
    logger.info("\n⚠️  Zones needing additional resources:")
    for row in delayed_zones:
        logger.info(f"   • {row['zone_id']}: {row['count']} delayed responses")
    
    # Peak hours
    peak_hours = df.groupBy("hour") \
        .count() \
        .orderBy(desc("count")) \
        .limit(5) \
        .collect()
    
    logger.info("\n⏰ Peak emergency hours:")
    for row in peak_hours:
        logger.info(f"   • Hour {row['hour']:02d}:00 - {row['count']} calls")
    
    # Critical event types
    critical_events = df.filter(col("priority_level") == "Critical") \
        .groupBy("event_type_id") \
        .count() \
        .orderBy(desc("count")) \
        .limit(3) \
        .collect()
    
    logger.info("\n🔴 Most common critical emergencies:")
    for row in critical_events:
        logger.info(f"   • {row['event_type_id']}: {row['count']} incidents")


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
    logger.info("\nEmergency Statistics:")
    features_df.select(
        avg("response_time_minutes").alias("avg_response"),
        min("response_time_minutes").alias("min_response"),
        max("response_time_minutes").alias("max_response"),
        sum("is_delayed").alias("delayed_count")
    ).show()
    
    # Train models
    response_model = train_response_time_model(features_df)
    quality_model = train_priority_classifier(features_df)
    
    # Analyze patterns
    analyze_patterns(features_df)
    
    # Generate recommendations
    generate_recommendations(features_df)
    
    # Save models
    logger.info(f"\nSaving models to {MODEL_PATH}...")
    response_model.write().overwrite().save(f"{MODEL_PATH}_response")
    quality_model.write().overwrite().save(f"{MODEL_PATH}_quality")
    logger.info("✓ Models saved!")
    
    logger.info("")
    logger.info("=" * 80)
    logger.info("🚨 Emergency Prediction Model Training Complete!")
    logger.info("=" * 80)
    logger.info("")
    logger.info("Use cases:")
    logger.info("  • Predict response times")
    logger.info("  • Optimize resource allocation")
    logger.info("  • Identify emergency hotspots")
    logger.info("  • Improve service quality")
    logger.info("")

except Exception as e:
    logger.error(f"Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    spark.stop()
