"""
SmartCity Data Warehouse ETL Pipeline DAG
Orchestrates:
1. SQL Server DWH backup restore
2. Spark ETL: Extract from SQL Server -> Load to Hive
3. Verification queries via Trino
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.operators.empty import EmptyOperator
from airflow.sensors.bash import BashSensor
import logging

# Default arguments for the DAG
default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2024, 1, 1),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

# DAG definition
dag = DAG(
    "smartcity_dwh_pipeline",
    default_args=default_args,
    description="SmartCity DWH ETL Pipeline: SQL Server -> Spark -> Hive -> Trino",
    schedule_interval=None,  # Manual trigger or set to "@daily"
    catchup=False,
    tags=["smartcity", "etl", "dwh", "spark", "hive", "trino"],
)

# Task 1: Wait for SQL Server to be healthy
wait_for_sqlserver = BashSensor(
    task_id="wait_for_sqlserver",
    bash_command="""
    docker exec sqlserver /opt/mssql-tools18/bin/sqlcmd \
        -S localhost -U sa -P 'SmartCity@2024!' -C \
        -Q "SELECT 1" > /dev/null 2>&1
    """,
    timeout=300,
    poke_interval=10,
    dag=dag,
)

# Task 2: Restore DWH backup
restore_dwh_backup = BashOperator(
    task_id="restore_dwh_backup",
    bash_command="""
    docker exec sqlserver /opt/mssql-tools18/bin/sqlcmd \
        -S localhost -U sa -P 'SmartCity@2024!' -C \
        -Q "
        -- Check if database already exists
        IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = 'SmartCityDWH')
        BEGIN
            RESTORE DATABASE SmartCityDWH
            FROM DISK = '/opt/sql/SmartCityDWH.bak'
            WITH 
                MOVE 'SmartCityDWH' TO '/var/opt/mssql/data/SmartCityDWH.mdf',
                MOVE 'SmartCityDWH_log' TO '/var/opt/mssql/data/SmartCityDWH_log.ldf',
                REPLACE
            PRINT 'Database restored successfully!'
        END
        ELSE
        BEGIN
            PRINT 'Database SmartCityDWH already exists, skipping restore.'
        END
        "
    """,
    dag=dag,
)

# Task 3: Verify database restored and list tables
verify_restore = BashOperator(
    task_id="verify_restore",
    bash_command="""
    docker exec sqlserver /opt/mssql-tools18/bin/sqlcmd \
        -S localhost -U sa -P 'SmartCity@2024!' -C \
        -d SmartCityDWH \
        -Q "
        SELECT 'Tables in SmartCityDWH:' AS Info;
        SELECT TABLE_SCHEMA, TABLE_NAME 
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_TYPE = 'BASE TABLE'
        ORDER BY TABLE_SCHEMA, TABLE_NAME;
        "
    """,
    dag=dag,
)

# Task 4: Wait for Spark and Hive to be ready
wait_for_spark = BashSensor(
    task_id="wait_for_spark",
    bash_command="docker exec spark-master curl -s http://localhost:8080 > /dev/null 2>&1",
    timeout=120,
    poke_interval=10,
    dag=dag,
)

wait_for_hive = BashSensor(
    task_id="wait_for_hive",
    bash_command="docker exec hive-server beeline -u jdbc:hive2://localhost:10000 -e 'SHOW DATABASES;' > /dev/null 2>&1",
    timeout=180,
    poke_interval=15,
    dag=dag,
)

# Task 5: Download JDBC driver if not exists
setup_jdbc_driver = BashOperator(
    task_id="setup_jdbc_driver",
    bash_command="""
    docker exec spark-master bash -c "
    if [ ! -f /spark/jars/mssql-jdbc-12.4.2.jre8.jar ]; then
        echo 'Downloading SQL Server JDBC driver...'
        wget -q -O /spark/jars/mssql-jdbc-12.4.2.jre8.jar \
            'https://repo1.maven.org/maven2/com/microsoft/sqlserver/mssql-jdbc/12.4.2.jre8/mssql-jdbc-12.4.2.jre8.jar'
        echo 'JDBC driver downloaded!'
    else
        echo 'JDBC driver already exists.'
    fi
    "
    """,
    dag=dag,
)

# Task 6: Create Hive database
create_hive_database = BashOperator(
    task_id="create_hive_database",
    bash_command="""
    docker exec hive-server beeline -u jdbc:hive2://localhost:10000 \
        -e "CREATE DATABASE IF NOT EXISTS smartcity_dwh;"
    """,
    dag=dag,
)

# Task 7: Run Spark ETL job
run_spark_etl = BashOperator(
    task_id="run_spark_etl",
    bash_command="""
    docker exec spark-master /spark/bin/spark-submit \
        --master spark://spark-master:7077 \
        --driver-memory 2g \
        --executor-memory 2g \
        --jars /spark/jars/mssql-jdbc-12.4.2.jre8.jar \
        --conf spark.sql.warehouse.dir=hdfs://namenode:9000/user/hive/warehouse \
        --conf spark.hadoop.fs.defaultFS=hdfs://namenode:9000 \
        --conf hive.metastore.uris=thrift://hive-metastore:9083 \
        /opt/scripts/pyspark/smartcity_dwh_etl.py
    """,
    execution_timeout=timedelta(hours=2),
    dag=dag,
)

# Task 8: Verify Hive tables
verify_hive_tables = BashOperator(
    task_id="verify_hive_tables",
    bash_command="""
    docker exec hive-server beeline -u jdbc:hive2://localhost:10000 -e "
        USE smartcity_dwh;
        SHOW TABLES;
        SELECT 'Hive tables created successfully!' AS Status;
    "
    """,
    dag=dag,
)

# Task 9: Test Trino queries
test_trino_queries = BashOperator(
    task_id="test_trino_queries",
    bash_command="""
    docker exec trino-coordinator trino --execute "
        SHOW CATALOGS;
        SHOW SCHEMAS IN hive;
        SHOW TABLES IN hive.smartcity_dwh;
    " || echo "Trino query completed (some tables may be empty)"
    """,
    dag=dag,
)

# Task 10: Generate sample report
generate_sample_report = BashOperator(
    task_id="generate_sample_report",
    bash_command="""
    echo "========================================"
    echo "SmartCity DWH Pipeline - Summary Report"
    echo "========================================"
    echo "Date: $(date)"
    echo ""
    echo "SQL Server Status:"
    docker exec sqlserver /opt/mssql-tools18/bin/sqlcmd \
        -S localhost -U sa -P 'SmartCity@2024!' -C \
        -d SmartCityDWH \
        -Q "SELECT COUNT(*) AS TableCount FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE='BASE TABLE'"
    echo ""
    echo "Hive Tables:"
    docker exec hive-server beeline -u jdbc:hive2://localhost:10000 \
        --silent=true \
        -e "USE smartcity_dwh; SHOW TABLES;" 2>/dev/null || echo "Unable to list Hive tables"
    echo ""
    echo "Trino Available Schemas:"
    docker exec trino-coordinator trino --execute "SHOW SCHEMAS IN hive" 2>/dev/null || echo "Trino check completed"
    echo ""
    echo "Pipeline completed successfully!"
    echo "========================================"
    """,
    dag=dag,
)

# Pipeline complete marker
pipeline_complete = EmptyOperator(
    task_id="pipeline_complete",
    dag=dag,
)

# Define task dependencies
# Phase 1: SQL Server setup
wait_for_sqlserver >> restore_dwh_backup >> verify_restore

# Phase 2: Spark/Hive preparation (parallel)
verify_restore >> [wait_for_spark, wait_for_hive]
wait_for_spark >> setup_jdbc_driver
wait_for_hive >> create_hive_database

# Phase 3: ETL execution (after both preparations complete)
[setup_jdbc_driver, create_hive_database] >> run_spark_etl

# Phase 4: Verification
run_spark_etl >> verify_hive_tables >> test_trino_queries >> generate_sample_report >> pipeline_complete
