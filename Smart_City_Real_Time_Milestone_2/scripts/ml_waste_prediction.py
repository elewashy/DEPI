#!/usr/bin/env python3
"""
Smart City ML - Waste Collection Optimization
Predicts fill levels and optimizes collection routes
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
from pyspark.ml.feature import VectorAssembler, StringIndexer, StandardScaler
from pyspark.ml.regression import RandomForestRegressor
from pyspark.ml.classification import LogisticRegression
from pyspark.ml.evaluation import RegressionEvaluator, BinaryClassificationEvaluator
from pyspark.ml import Pipeline
import logging
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
KAFKA_BROKER = "kafka:9092"
HDFS_NAMENODE = "hdfs://namenode:9000"
MODEL_PATH = "/tmp/models/waste_prediction"

# Create Spark session
spark = SparkSession.builder \
    .appName("SmartCityWasteML") \
    .config("spark.sql.shuffle.partitions", "4") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")

logger.info("=" * 80)
logger.info("🗑️  Smart City ML - Waste Collection Optimization")
logger.info("=" * 80)
logger.info("")

# Schema
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


def load_data():
    """Load waste collection data"""
    hdfs_path = f"{HDFS_NAMENODE}/smartcity/waste"
    
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
            .option("subscribe", "waste") \
            .option("startingOffsets", "earliest") \
            .option("endingOffsets", "latest") \
            .load()
        
        df = kafka_df.select(
            from_json(col("value").cast("string"), waste_schema).alias("data")
        ).select("data.*")
        
        logger.info(f"✓ Loaded {df.count():,} records from Kafka")
        return df


def engineer_features(df):
    """Create ML features for waste prediction"""
    logger.info("Engineering features...")
    
    features_df = df \
        .withColumn("hour", substring(col("time_key"), 1, 2).cast("int")) \
        .withColumn("day_of_week", 
            dayofweek(to_date(col("date_key").cast("string"), "yyyyMMdd"))) \
        .withColumn("is_weekend", 
            when((col("day_of_week") == 1) | (col("day_of_week") == 7), 1).otherwise(0)) \
        .withColumn("time_period",
            when(col("hour") < 6, 0)  # Early morning
            .when(col("hour") < 12, 1)  # Morning
            .when(col("hour") < 18, 2)  # Afternoon
            .otherwise(3)) \
        .withColumn("needs_collection", 
            when(col("fill_level_percent") > 80, 1).otherwise(0)) \
        .withColumn("is_critical", 
            when(col("fill_level_percent") > 90, 1).otherwise(0)) \
        .withColumn("fill_category",
            when(col("fill_level_percent") > 90, 3)  # Critical
            .when(col("fill_level_percent") > 70, 2)  # High
            .when(col("fill_level_percent") > 40, 1)  # Medium
            .otherwise(0)) \
        .filter(col("fill_level_percent").isNotNull())
    
    return features_df


def train_fill_prediction_model(df):
    """Train model to predict fill levels"""
    logger.info("")
    logger.info("=" * 60)
    logger.info("FILL LEVEL PREDICTION (Regression)")
    logger.info("=" * 60)
    
    # Indexers
    zone_indexer = StringIndexer(inputCol="zone_id", outputCol="zone_idx", handleInvalid="keep")
    building_indexer = StringIndexer(inputCol="building_id", outputCol="building_idx", handleInvalid="keep")
    container_indexer = StringIndexer(inputCol="container_id", outputCol="container_idx", handleInvalid="keep")
    
    feature_cols = [
        "zone_idx", "building_idx", "container_idx", "hour",
        "day_of_week", "is_weekend", "time_period"
    ]
    
    assembler = VectorAssembler(inputCols=feature_cols, outputCol="features_raw", handleInvalid="skip")
    scaler = StandardScaler(inputCol="features_raw", outputCol="features", withStd=True, withMean=False)
    
    rf = RandomForestRegressor(
        featuresCol="features",
        labelCol="fill_level_percent",
        numTrees=100,
        maxDepth=10,
        seed=42
    )
    
    pipeline = Pipeline(stages=[zone_indexer, building_indexer, container_indexer, assembler, scaler, rf])
    
    train_data, test_data = df.randomSplit([0.8, 0.2], seed=42)
    
    logger.info(f"Training: {train_data.count():,}, Testing: {test_data.count():,}")
    logger.info("Training Random Forest Regressor...")
    
    model = pipeline.fit(train_data)
    predictions = model.transform(test_data)
    
    # Evaluate
    rmse = RegressionEvaluator(labelCol="fill_level_percent", predictionCol="prediction", metricName="rmse").evaluate(predictions)
    r2 = RegressionEvaluator(labelCol="fill_level_percent", predictionCol="prediction", metricName="r2").evaluate(predictions)
    mae = RegressionEvaluator(labelCol="fill_level_percent", predictionCol="prediction", metricName="mae").evaluate(predictions)
    
    logger.info("")
    logger.info(f"R² Score:  {r2:.4f}")
    logger.info(f"RMSE:      {rmse:.4f}%")
    logger.info(f"MAE:       {mae:.4f}%")
    
    # Sample predictions
    logger.info("")
    logger.info("Sample Predictions:")
    predictions.select("zone_id", "building_id", "hour", "fill_level_percent", "prediction") \
        .withColumn("prediction", round(col("prediction"), 1)) \
        .show(10, truncate=False)
    
    return model


def train_collection_model(df):
    """Train model to predict if collection is needed"""
    logger.info("")
    logger.info("=" * 60)
    logger.info("COLLECTION NEED PREDICTION (Classification)")
    logger.info("=" * 60)
    
    # Indexers
    zone_indexer = StringIndexer(inputCol="zone_id", outputCol="zone_idx", handleInvalid="keep")
    building_indexer = StringIndexer(inputCol="building_id", outputCol="building_idx", handleInvalid="keep")
    container_indexer = StringIndexer(inputCol="container_id", outputCol="container_idx", handleInvalid="keep")
    
    feature_cols = [
        "zone_idx", "building_idx", "container_idx", "hour",
        "day_of_week", "is_weekend", "time_period"
    ]
    
    assembler = VectorAssembler(inputCols=feature_cols, outputCol="features", handleInvalid="skip")
    
    lr = LogisticRegression(
        featuresCol="features",
        labelCol="needs_collection",
        maxIter=100,
        regParam=0.01
    )
    
    pipeline = Pipeline(stages=[zone_indexer, building_indexer, container_indexer, assembler, lr])
    
    train_data, test_data = df.randomSplit([0.8, 0.2], seed=42)
    
    logger.info(f"Training: {train_data.count():,}, Testing: {test_data.count():,}")
    logger.info("Training Logistic Regression...")
    
    model = pipeline.fit(train_data)
    predictions = model.transform(test_data)
    
    # Evaluate
    auc = BinaryClassificationEvaluator(
        labelCol="needs_collection", 
        rawPredictionCol="rawPrediction", 
        metricName="areaUnderROC"
    ).evaluate(predictions)
    
    logger.info("")
    logger.info(f"AUC-ROC: {auc:.4f}")
    
    # Accuracy
    correct = predictions.filter(col("needs_collection") == col("prediction")).count()
    total = predictions.count()
    accuracy = correct / total if total > 0 else 0
    
    logger.info(f"Accuracy: {accuracy:.4f}")
    
    return model


def optimize_routes(df):
    """Generate route optimization recommendations"""
    logger.info("")
    logger.info("=" * 60)
    logger.info("ROUTE OPTIMIZATION ANALYSIS")
    logger.info("=" * 60)
    
    # Containers needing collection
    logger.info("\nContainers Needing Collection (>80% full):")
    urgent = df.filter(col("fill_level_percent") > 80) \
        .groupBy("zone_id") \
        .agg(
            count("*").alias("urgent_containers"),
            avg("fill_level_percent").alias("avg_fill")
        ) \
        .orderBy(desc("urgent_containers"))
    urgent.show(10, truncate=False)
    
    # Critical containers
    logger.info("\nCritical Containers (>90% full):")
    critical = df.filter(col("fill_level_percent") > 90) \
        .select("zone_id", "building_id", "container_id", "fill_level_percent") \
        .orderBy(desc("fill_level_percent"))
    critical.show(10, truncate=False)
    
    # Zone priority ranking
    logger.info("\nZone Collection Priority:")
    df.groupBy("zone_id") \
        .agg(
            avg("fill_level_percent").alias("avg_fill"),
            sum(when(col("fill_level_percent") > 80, 1).otherwise(0)).alias("urgent"),
            count("*").alias("total_containers")
        ) \
        .withColumn("priority_score", 
            col("avg_fill") * 0.4 + col("urgent") / col("total_containers") * 60) \
        .orderBy(desc("priority_score")) \
        .show(10, truncate=False)
    
    # Collection schedule recommendation
    logger.info("\nRecommended Collection Times by Zone:")
    df.groupBy("zone_id", "hour") \
        .agg(avg("fill_level_percent").alias("avg_fill")) \
        .filter(col("avg_fill") > 70) \
        .orderBy("zone_id", desc("avg_fill")) \
        .show(20, truncate=False)


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
    logger.info("\nWaste Collection Statistics:")
    features_df.select(
        avg("fill_level_percent").alias("avg_fill"),
        sum("needs_collection").alias("needs_collection"),
        sum("is_critical").alias("critical_count")
    ).show()
    
    # Train models
    fill_model = train_fill_prediction_model(features_df)
    collection_model = train_collection_model(features_df)
    
    # Route optimization
    optimize_routes(features_df)
    
    # Save models
    logger.info(f"\nSaving models to {MODEL_PATH}...")
    fill_model.write().overwrite().save(f"{MODEL_PATH}_fill")
    collection_model.write().overwrite().save(f"{MODEL_PATH}_collection")
    logger.info("✓ Models saved!")
    
    logger.info("")
    logger.info("=" * 80)
    logger.info("🗑️  Waste Prediction Model Training Complete!")
    logger.info("=" * 80)
    logger.info("")
    logger.info("Use cases:")
    logger.info("  • Predict container fill levels")
    logger.info("  • Optimize collection routes")
    logger.info("  • Reduce fuel consumption")
    logger.info("  • Prevent overflows")
    logger.info("")

except Exception as e:
    logger.error(f"Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    spark.stop()
