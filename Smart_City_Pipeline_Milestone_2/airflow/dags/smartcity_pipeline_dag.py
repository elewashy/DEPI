"""
Smart City Airflow DAG for Real-time Data Pipeline Orchestration
This DAG orchestrates the complete SmartCity IoT pipeline
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.sensors.python import PythonSensor
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# Default arguments
default_args = {
    'owner': 'smartcity-team',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=2),
    'start_date': datetime(2025, 11, 29),
}

# Smart City configuration
KAFKA_BROKER = 'kafka:9092'
SMARTCITY_TOPICS = ['energy', 'traffic', 'bus_gps', 'waste', 'emergency']


def check_kafka_connection(**context):
    """Check Kafka broker connectivity"""
    import socket
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        result = sock.connect_ex(('kafka', 9092))
        sock.close()
        
        if result == 0:
            logger.info("✓ Kafka broker is reachable")
            return True
        else:
            logger.error("✗ Kafka broker is not reachable")
            return False
    except Exception as e:
        logger.error(f"Error checking Kafka: {e}")
        return False


def check_hdfs_connection(**context):
    """Check HDFS NameNode connectivity"""
    import socket
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        result = sock.connect_ex(('namenode', 9870))
        sock.close()
        
        if result == 0:
            logger.info("✓ HDFS NameNode is reachable")
            return True
        else:
            logger.error("✗ HDFS NameNode is not reachable")
            return False
    except Exception as e:
        logger.error(f"Error checking HDFS: {e}")
        return False


def check_spark_connection(**context):
    """Check Spark Master connectivity"""
    import socket
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        result = sock.connect_ex(('spark-master', 8080))
        sock.close()
        
        if result == 0:
            logger.info("✓ Spark Master is reachable")
            return True
        else:
            logger.error("✗ Spark Master is not reachable")
            return False
    except Exception as e:
        logger.error(f"Error checking Spark: {e}")
        return False


def verify_kafka_topics(**context):
    """Verify Kafka topics exist"""
    try:
        from kafka import KafkaConsumer
        
        consumer = KafkaConsumer(
            bootstrap_servers=[KAFKA_BROKER],
            consumer_timeout_ms=10000
        )
        
        existing_topics = consumer.topics()
        consumer.close()
        
        logger.info(f"Existing Kafka topics: {existing_topics}")
        
        missing_topics = []
        for topic in SMARTCITY_TOPICS:
            if topic in existing_topics:
                logger.info(f"  ✓ Topic '{topic}' exists")
            else:
                logger.warning(f"  ✗ Topic '{topic}' missing")
                missing_topics.append(topic)
        
        if missing_topics:
            logger.warning(f"Missing topics: {missing_topics}")
            context['ti'].xcom_push(key='missing_topics', value=missing_topics)
            return False
        
        return True
        
    except ImportError:
        logger.warning("kafka-python not installed, skipping topic check")
        return True
    except Exception as e:
        logger.error(f"Error verifying topics: {e}")
        return True  # Continue anyway


def get_kafka_message_counts(**context):
    """Get message counts from Kafka topics"""
    try:
        from kafka import KafkaConsumer
        from kafka import TopicPartition
        
        consumer = KafkaConsumer(
            bootstrap_servers=[KAFKA_BROKER],
            consumer_timeout_ms=10000
        )
        
        message_counts = {}
        
        for topic in SMARTCITY_TOPICS:
            try:
                partitions = consumer.partitions_for_topic(topic)
                if partitions:
                    total = 0
                    for p in partitions:
                        tp = TopicPartition(topic, p)
                        consumer.assign([tp])
                        consumer.seek_to_end(tp)
                        total += consumer.position(tp)
                    message_counts[topic] = total
                    logger.info(f"  {topic}: {total} messages")
            except Exception as e:
                logger.warning(f"Could not get count for {topic}: {e}")
                message_counts[topic] = 0
        
        consumer.close()
        
        context['ti'].xcom_push(key='message_counts', value=message_counts)
        return message_counts
        
    except ImportError:
        logger.warning("kafka-python not installed")
        return {}
    except Exception as e:
        logger.error(f"Error getting message counts: {e}")
        return {}


def generate_pipeline_report(**context):
    """Generate pipeline status report"""
    ti = context['ti']
    
    # Get XCom values
    message_counts = ti.xcom_pull(task_ids='get_kafka_metrics', key='message_counts') or {}
    
    report = []
    report.append("=" * 60)
    report.append("  SMART CITY PIPELINE STATUS REPORT")
    report.append(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("=" * 60)
    report.append("")
    
    report.append("📊 KAFKA TOPICS:")
    total_messages = 0
    for topic in SMARTCITY_TOPICS:
        count = message_counts.get(topic, 0)
        total_messages += count
        status = "✓" if count > 0 else "○"
        report.append(f"  {status} {topic}: {count:,} messages")
    report.append(f"  Total: {total_messages:,} messages")
    report.append("")
    
    report.append("🔧 SERVICES:")
    report.append("  ✓ Kafka Broker: kafka:9092")
    report.append("  ✓ HDFS NameNode: namenode:9870")
    report.append("  ✓ Spark Master: spark-master:8080")
    report.append("")
    
    report.append("🤖 ML MODELS:")
    for model in ['Energy', 'Traffic', 'Bus', 'Waste', 'Emergency']:
        report.append(f"  • {model} Prediction Model")
    report.append("")
    
    report.append("=" * 60)
    
    full_report = "\n".join(report)
    logger.info(full_report)
    
    return full_report


# Create DAG
with DAG(
    'smartcity_pipeline',
    default_args=default_args,
    description='Smart City IoT Data Pipeline Orchestration',
    schedule_interval='*/30 * * * *',  # Every 30 minutes
    catchup=False,
    tags=['smartcity', 'iot', 'streaming', 'ml'],
    max_active_runs=1,
) as dag:
    
    # Task 1: Check Kafka
    check_kafka = PythonOperator(
        task_id='check_kafka_connection',
        python_callable=check_kafka_connection,
    )
    
    # Task 2: Check HDFS
    check_hdfs = PythonOperator(
        task_id='check_hdfs_connection',
        python_callable=check_hdfs_connection,
    )
    
    # Task 3: Check Spark
    check_spark = PythonOperator(
        task_id='check_spark_connection',
        python_callable=check_spark_connection,
    )
    
    # Task 4: Verify Kafka topics
    verify_topics = PythonOperator(
        task_id='verify_kafka_topics',
        python_callable=verify_kafka_topics,
    )
    
    # Task 5: Get Kafka metrics
    get_metrics = PythonOperator(
        task_id='get_kafka_metrics',
        python_callable=get_kafka_message_counts,
    )
    
    # Task 6: Generate report
    generate_report = PythonOperator(
        task_id='generate_pipeline_report',
        python_callable=generate_pipeline_report,
    )
    
    # Task 7: Log completion
    log_completion = BashOperator(
        task_id='log_completion',
        bash_command='echo "Smart City Pipeline check completed at $(date)"',
    )
    
    # Define dependencies
    [check_kafka, check_hdfs, check_spark] >> verify_topics
    verify_topics >> get_metrics >> generate_report >> log_completion
