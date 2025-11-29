#!/usr/bin/env python3
"""
Smart City ML - Energy Consumption Prediction
Trains a model to predict energy consumption patterns
Uses RandomForest for regression and detects anomalies
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
from pyspark.ml.feature import VectorAssembler, StringIndexer, StandardScaler
from pyspark.ml.regression import RandomForestRegressor, GBTRegressor
from pyspark.ml.evaluation import RegressionEvaluator
from pyspark.ml import Pipeline
import logging
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
KAFKA_BROKER = "kafka:9092"
HDFS_NAMENODE = "hdfs://namenode:9000"
MODEL_PATH = "/tmp/models/energy_prediction"

# Create Spark session
spark = SparkSession.builder \
    .appName("SmartCityEnergyML") \
    .config("spark.sql.shuffle.partitions", "4") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")

logger.info("=" * 80)
logger.info("🔌 Smart City ML - Energy Consumption Prediction")
logger.info("=" * 80)
logger.info("")

# Schema for energy data
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


def load_data():
    """Load data from HDFS or Kafka"""
    hdfs_path = f"{HDFS_NAMENODE}/smartcity/energy"
    
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
            .option("subscribe", "energy") \
            .option("startingOffsets", "earliest") \
            .option("endingOffsets", "latest") \
            .load()
        
        df = kafka_df.select(
            from_json(col("value").cast("string"), energy_schema).alias("data")
        ).select("data.*")
        
        logger.info(f"✓ Loaded {df.count():,} records from Kafka")
        return df


def engineer_features(df):
    """Create ML features from raw data"""
    logger.info("Engineering features...")
    
    features_df = df \
        .withColumn("hour", substring(col("time_key"), 1, 2).cast("int")) \
        .withColumn("minute", substring(col("time_key"), 3, 2).cast("int")) \
        .withColumn("day_of_week", 
            dayofweek(to_date(col("date_key").cast("string"), "yyyyMMdd"))) \
        .withColumn("is_peak_hour", 
            when((col("hour") >= 8) & (col("hour") <= 18), 1).otherwise(0)) \
        .withColumn("is_evening_peak", 
            when((col("hour") >= 18) & (col("hour") <= 22), 1).otherwise(0)) \
        .withColumn("is_night", 
            when((col("hour") >= 0) & (col("hour") <= 5), 1).otherwise(0)) \
        .withColumn("is_weekend", 
            when((col("day_of_week") == 1) | (col("day_of_week") == 7), 1).otherwise(0)) \
        .withColumn("voltage_normalized", col("voltage") / 230.0) \
        .withColumn("power_factor", 
            when(col("voltage") * col("current") > 0, 
                 col("kwh") * 1000 / (col("voltage") * col("current")))
            .otherwise(1.0)) \
        .filter(col("quality_flag") == "GOOD")
    
    return features_df


def train_model(df):
    """Train the energy prediction model"""
    # Index categorical features
    building_indexer = StringIndexer(
        inputCol="building_id", 
        outputCol="building_idx",
        handleInvalid="keep"
    )
    device_indexer = StringIndexer(
        inputCol="device_id", 
        outputCol="device_idx",
        handleInvalid="keep"
    )
    
    # Feature columns
    feature_cols = [
        "building_idx", "device_idx", "hour", "minute",
        "day_of_week", "is_peak_hour", "is_evening_peak",
        "is_night", "is_weekend", "voltage_normalized", "current"
    ]
    
    assembler = VectorAssembler(
        inputCols=feature_cols, 
        outputCol="features_raw",
        handleInvalid="skip"
    )
    
    scaler = StandardScaler(
        inputCol="features_raw",
        outputCol="features",
        withStd=True,
        withMean=False
    )
    
    # Random Forest Regressor
    rf = RandomForestRegressor(
        featuresCol="features",
        labelCol="kwh",
        numTrees=100,
        maxDepth=12,
        maxBins=100,
        seed=42
    )
    
    # Create pipeline
    pipeline = Pipeline(stages=[
        building_indexer, device_indexer, 
        assembler, scaler, rf
    ])
    
    # Split data
    train_data, test_data = df.randomSplit([0.8, 0.2], seed=42)
    
    logger.info(f"Training set: {train_data.count():,} records")
    logger.info(f"Test set: {test_data.count():,} records")
    logger.info("")
    logger.info("Training Random Forest model...")
    
    # Train
    model = pipeline.fit(train_data)
    
    # Evaluate
    predictions = model.transform(test_data)
    
    evaluators = {
        "RMSE": RegressionEvaluator(labelCol="kwh", predictionCol="prediction", metricName="rmse"),
        "R2": RegressionEvaluator(labelCol="kwh", predictionCol="prediction", metricName="r2"),
        "MAE": RegressionEvaluator(labelCol="kwh", predictionCol="prediction", metricName="mae")
    }
    
    metrics = {name: eval.evaluate(predictions) for name, eval in evaluators.items()}
    
    logger.info("")
    logger.info("=" * 60)
    logger.info("MODEL PERFORMANCE")
    logger.info("=" * 60)
    logger.info(f"R² Score:      {metrics['R2']:.4f}")
    logger.info(f"RMSE:          {metrics['RMSE']:.4f} kWh")
    logger.info(f"MAE:           {metrics['MAE']:.4f} kWh")
    logger.info("=" * 60)
    
    # Feature importance
    rf_model = model.stages[-1]
    importance = rf_model.featureImportances.toArray()
    
    logger.info("")
    logger.info("Feature Importance:")
    for i, col_name in enumerate(feature_cols):
        logger.info(f"  {col_name:20s}: {importance[i]:.4f}")
    
    # Sample predictions
    logger.info("")
    logger.info("Sample Predictions:")
    predictions.select(
        "building_id", "hour", "kwh", "prediction",
        ((col("prediction") - col("kwh")) / col("kwh") * 100).alias("error_%")
    ).show(10, truncate=False)
    
    return model, metrics


def detect_anomalies(df, model):
    """Detect anomalous energy consumption"""
    predictions = model.transform(df)
    
    # Calculate prediction error
    anomalies = predictions \
        .withColumn("error", abs(col("prediction") - col("kwh"))) \
        .withColumn("error_pct", col("error") / col("kwh") * 100)
    
    # Flag anomalies (>50% error or very high consumption)
    anomalies = anomalies \
        .withColumn("is_anomaly", 
            when((col("error_pct") > 50) | (col("kwh") > 50), 1).otherwise(0))
    
    anomaly_count = anomalies.filter(col("is_anomaly") == 1).count()
    total_count = anomalies.count()
    
    logger.info("")
    logger.info("=" * 60)
    logger.info("ANOMALY DETECTION")
    logger.info("=" * 60)
    logger.info(f"Total records analyzed: {total_count:,}")
    logger.info(f"Anomalies detected: {anomaly_count:,}")
    logger.info(f"Anomaly rate: {anomaly_count/total_count*100:.2f}%")
    
    if anomaly_count > 0:
        logger.info("")
        logger.info("Sample Anomalies:")
        anomalies.filter(col("is_anomaly") == 1) \
            .select("building_id", "device_id", "hour", "kwh", "prediction", "error_pct") \
            .show(10, truncate=False)
    
    return anomalies


# Main execution
try:
    # Load data
    raw_data = load_data()
    
    if raw_data.count() == 0:
        logger.error("No data available! Run the data producer first.")
        spark.stop()
        sys.exit(1)
    
    # Engineer features
    features_df = engineer_features(raw_data)
    
    if features_df.count() == 0:
        logger.error("No valid data after filtering!")
        spark.stop()
        sys.exit(1)
    
    logger.info(f"Features engineered: {features_df.count():,} records")
    logger.info("")
    
    # Show data statistics
    logger.info("Energy Statistics:")
    features_df.select(
        avg("kwh").alias("avg_kwh"),
        min("kwh").alias("min_kwh"),
        max("kwh").alias("max_kwh"),
        stddev("kwh").alias("std_kwh")
    ).show()
    
    # Train model
    model, metrics = train_model(features_df)
    
    # Save model
    logger.info(f"\nSaving model to {MODEL_PATH}...")
    model.write().overwrite().save(MODEL_PATH)
    logger.info("✓ Model saved successfully!")
    
    # Detect anomalies
    anomalies = detect_anomalies(features_df, model)
    
    logger.info("")
    logger.info("=" * 80)
    logger.info("🔌 Energy Prediction Model Training Complete!")
    logger.info("=" * 80)
    logger.info("")
    logger.info("Use cases:")
    logger.info("  • Predict peak energy demand")
    logger.info("  • Detect anomalous consumption")
    logger.info("  • Optimize energy distribution")
    logger.info("  • Building efficiency scoring")
    logger.info("")

except Exception as e:
    logger.error(f"Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    spark.stop()
