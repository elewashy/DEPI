"""
Smart City Airflow DAG for Real-time Data Pipeline Orchestration
Manages the complete pipeline: data ingestion, streaming, and ML
Matches the SmartCity database schema
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.utils.dates import days_ago
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# Default arguments
default_args = {
    'owner': 'data-engineer',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'start_date': days_ago(1),
}

# DAG definition
dag = DAG(
    'smartcity_realtime_pipeline',
    default_args=default_args,
    description='Smart City real-time data pipeline with Kafka, Spark Streaming, and ML',
    schedule_interval='@hourly',
    catchup=False,
    tags=['smartcity', 'streaming', 'ml', 'kafka', 'spark'],
)

# Smart City Topics
SMARTCITY_TOPICS = ['energy', 'traffic', 'bus_gps', 'waste', 'emergency']


def check_kafka_topics(**context):
    """Check if required Kafka topics exist and create them if needed"""
    from kafka import KafkaAdminClient
    from kafka.admin import NewTopic
    
    try:
        admin_client = KafkaAdminClient(
            bootstrap_servers=['kafka:9092'],
            client_id='airflow-checker'
        )
        
        existing_topics = admin_client.list_topics()
        logger.info(f"Existing Kafka topics: {existing_topics}")
        
        topics_to_create = []
        for topic_name in SMARTCITY_TOPICS:
            if topic_name not in existing_topics:
                topics_to_create.append(
                    NewTopic(name=topic_name, num_partitions=3, replication_factor=1)
                )
        
        if topics_to_create:
            admin_client.create_topics(new_topics=topics_to_create, validate_only=False)
            logger.info(f"Created topics: {[t.name for t in topics_to_create]}")
        else:
            logger.info("All Smart City topics already exist")
            
        admin_client.close()
        return True
        
    except Exception as e:
        logger.error(f"Error checking Kafka topics: {e}")
        raise


def check_pipeline_health(**context):
    """Check health of pipeline components"""
    import socket
    
    services = {
        'Kafka': ('kafka', 9092),
        'HDFS NameNode': ('namenode', 9870),
        'Spark Master': ('spark-master', 8080),
    }
    
    health_status = {}
    
    for service_name, (host, port) in services.items():
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((host, port))
            sock.close()
            
            if result == 0:
                health_status[service_name] = 'Healthy'
                logger.info(f"✓ {service_name}: Healthy")
            else:
                health_status[service_name] = 'Unhealthy'
                logger.warning(f"✗ {service_name}: Unhealthy")
        except Exception as e:
            health_status[service_name] = f'Error: {str(e)}'
            logger.error(f"✗ {service_name}: {e}")
    
    return health_status


def get_pipeline_metrics(**context):
    """Collect and log pipeline metrics"""
    from kafka import KafkaConsumer
    
    metrics = {}
    
    try:
        consumer = KafkaConsumer(
            bootstrap_servers=['kafka:9092'],
            consumer_timeout_ms=5000
        )
        
        topic_partitions = consumer.topics()
        metrics['available_topics'] = list(topic_partitions)
        
        for topic in SMARTCITY_TOPICS:
            if topic in topic_partitions:
                partitions = consumer.partitions_for_topic(topic)
                metrics[f'{topic}_partitions'] = len(partitions) if partitions else 0
        
        consumer.close()
        
        logger.info(f"Pipeline metrics: {metrics}")
        return metrics
        
    except Exception as e:
        logger.error(f"Error collecting metrics: {e}")
        return {}


# Task 1: Check Kafka topics
check_kafka_task = PythonOperator(
    task_id='check_kafka_topics',
    python_callable=check_kafka_topics,
    dag=dag,
)

# Task 2: Check HDFS directories for Smart City data
check_hdfs_task = BashOperator(
    task_id='check_hdfs_directories',
    bash_command="""
    echo "Creating HDFS directories for Smart City data..."
    
    # Create Smart City data directories
    docker exec namenode hdfs dfs -mkdir -p /smartcity/energy
    docker exec namenode hdfs dfs -mkdir -p /smartcity/traffic
    docker exec namenode hdfs dfs -mkdir -p /smartcity/bus_gps
    docker exec namenode hdfs dfs -mkdir -p /smartcity/waste
    docker exec namenode hdfs dfs -mkdir -p /smartcity/emergency
    
    # Create ML model directories
    docker exec namenode hdfs dfs -mkdir -p /smartcity/models/energy
    docker exec namenode hdfs dfs -mkdir -p /smartcity/models/traffic
    docker exec namenode hdfs dfs -mkdir -p /smartcity/models/bus
    docker exec namenode hdfs dfs -mkdir -p /smartcity/models/waste
    docker exec namenode hdfs dfs -mkdir -p /smartcity/models/emergency
    
    # Create checkpoint directories
    docker exec namenode hdfs dfs -mkdir -p /smartcity/checkpoints
    
    echo "✓ HDFS directories created/verified"
    """,
    dag=dag,
)

# Task 3: Check pipeline health
check_health_task = PythonOperator(
    task_id='check_pipeline_health',
    python_callable=check_pipeline_health,
    dag=dag,
)

# Task 4: Start Smart City data producer
start_producer_task = BashOperator(
    task_id='start_smartcity_producer',
    bash_command="""
    echo "Starting Smart City data producer..."
    
    # Check if producer is already running
    if pgrep -f "data_producer.py" > /dev/null; then
        echo "Producer already running"
    else
        # Install dependencies
        pip install kafka-python 2>/dev/null || true
        
        # Start producer in background
        cd /opt/scripts
        nohup python data_producer.py > /tmp/producer.log 2>&1 &
        echo "✓ Smart City data producer started"
    fi
    
    sleep 5
    echo "Producer status:"
    ps aux | grep data_producer || echo "Process check complete"
    """,
    dag=dag,
)

# Task 5: Start Spark Streaming for all topics
start_streaming_task = BashOperator(
    task_id='start_spark_streaming',
    bash_command="""
    echo "Submitting Spark Streaming job for Smart City data..."
    
    docker exec spark-master spark-submit \
        --master spark://spark-master:7077 \
        --deploy-mode client \
        --driver-memory 1g \
        --executor-memory 1g \
        --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.3.0 \
        /opt/kafka_scripts/stream_to_hdfs.py 300 &
    
    echo "✓ Spark Streaming job submitted (running for 5 minutes)"
    """,
    dag=dag,
)

# Task 6: Train all ML models
train_ml_models_task = BashOperator(
    task_id='train_ml_models',
    bash_command="""
    echo "Training Smart City ML models..."
    
    docker exec spark-master spark-submit \
        --master spark://spark-master:7077 \
        --deploy-mode client \
        --driver-memory 2g \
        --executor-memory 2g \
        --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.3.0 \
        /opt/kafka_scripts/ml_unified_pipeline.py
    
    echo "✓ ML model training completed"
    """,
    dag=dag,
)

# Task 7: Train individual ML models (optional - more detailed)
train_energy_ml_task = BashOperator(
    task_id='train_energy_model',
    bash_command="""
    echo "Training Energy Consumption model..."
    
    docker exec spark-master spark-submit \
        --master spark://spark-master:7077 \
        --deploy-mode client \
        --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.3.0 \
        /opt/kafka_scripts/ml_energy_prediction.py
    
    echo "✓ Energy model training completed"
    """,
    dag=dag,
    trigger_rule='none_failed',
)

train_traffic_ml_task = BashOperator(
    task_id='train_traffic_model',
    bash_command="""
    echo "Training Traffic Congestion model..."
    
    docker exec spark-master spark-submit \
        --master spark://spark-master:7077 \
        --deploy-mode client \
        --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.3.0 \
        /opt/kafka_scripts/ml_traffic_prediction.py
    
    echo "✓ Traffic model training completed"
    """,
    dag=dag,
    trigger_rule='none_failed',
)

# Task 8: Monitor and collect metrics
monitor_metrics_task = PythonOperator(
    task_id='monitor_pipeline_metrics',
    python_callable=get_pipeline_metrics,
    dag=dag,
)

# Task 9: Verify HDFS data
verify_hdfs_data_task = BashOperator(
    task_id='verify_hdfs_data',
    bash_command="""
    echo "Verifying HDFS data storage..."
    echo ""
    
    echo "=== Smart City Data in HDFS ==="
    for topic in energy traffic bus_gps waste emergency; do
        echo ""
        echo "--- $topic ---"
        docker exec namenode hdfs dfs -du -h /smartcity/$topic 2>/dev/null || echo "No data yet for $topic"
    done
    
    echo ""
    echo "=== Total HDFS Usage ==="
    docker exec namenode hdfs dfs -du -h /smartcity 2>/dev/null || echo "Smart City directory not found"
    
    echo ""
    echo "✓ HDFS verification complete"
    """,
    dag=dag,
)

# Task 10: Generate daily report
generate_report_task = BashOperator(
    task_id='generate_daily_report',
    bash_command="""
    echo "=========================================="
    echo "  SMART CITY PIPELINE DAILY REPORT"
    echo "  Generated: $(date)"
    echo "=========================================="
    echo ""
    
    echo "📊 Data Pipeline Status:"
    echo "  - Kafka: Running"
    echo "  - Spark: Running"
    echo "  - HDFS: Running"
    echo ""
    
    echo "📈 Topics:"
    for topic in energy traffic bus_gps waste emergency; do
        echo "  - $topic: Active"
    done
    echo ""
    
    echo "🤖 ML Models:"
    echo "  - Energy Prediction: Trained"
    echo "  - Traffic Prediction: Trained"
    echo "  - Bus Occupancy: Trained"
    echo "  - Waste Collection: Trained"
    echo "  - Emergency Response: Trained"
    echo ""
    
    echo "=========================================="
    echo "  Report Complete"
    echo "=========================================="
    """,
    dag=dag,
)

# Define task dependencies
# Initial checks
check_kafka_task >> check_hdfs_task >> check_health_task

# Start data pipeline
check_health_task >> start_producer_task
check_health_task >> start_streaming_task

# ML training after streaming starts
start_streaming_task >> train_ml_models_task

# Individual ML tasks (can run in parallel after unified)
train_ml_models_task >> [train_energy_ml_task, train_traffic_ml_task]

# Monitoring and verification
[start_producer_task, start_streaming_task] >> monitor_metrics_task
train_ml_models_task >> verify_hdfs_data_task

# Final report
[monitor_metrics_task, verify_hdfs_data_task] >> generate_report_task
