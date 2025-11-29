"""
Smart City ETL Pipeline DAG

This DAG orchestrates the ETL process for Smart City data warehouse.
It uses a single unified Talend job that loads all dimension and fact tables.

Architecture:
- Single master job that runs all ETL processes in correct order
- Includes all dimension and fact table loads
- Handles dependencies internally within Talend

Schedule: Daily at 2 AM
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
import subprocess
from datetime import datetime, timedelta

def run_all_smart_city_jobs():
    """Function to run the unified Smart City ETL job"""
    script_path = '/opt/airflow/jobs/Run_All_Jobs_Smart_City_ETL/Run_All_Jobs_Smart_City_ETL_run.sh'
    working_dir = '/opt/airflow/jobs/Run_All_Jobs_Smart_City_ETL'
    
    try:
        result = subprocess.run(
            ['bash', script_path],
            cwd=working_dir,
            capture_output=True,
            text=True,
            check=True
        )
        print(f"ETL Process Output: {result.stdout}")
        if result.stderr:
            print(f"ETL Process Warnings: {result.stderr}")
        return result.returncode
    except subprocess.CalledProcessError as e:
        print(f"ETL Process Failed: {e}")
        print(f"Return code: {e.returncode}")
        print(f"Output: {e.stdout}")
        print(f"Error: {e.stderr}")
        raise

# Default arguments for the DAG
default_args = {
    'owner': 'smart_city_team',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'execution_timeout': timedelta(hours=2),
}

# Define the DAG
with DAG(
    dag_id='smart_city_etl',
    default_args=default_args,
    description='Smart City ETL Pipeline - Unified Job for All Tables',
    schedule_interval='0 2 * * *',  # Runs daily at 2 AM
    start_date=datetime(2025, 9, 29),
    catchup=False,
    tags=['smart_city', 'etl', 'talend', 'unified'],
) as dag:

    # Single unified task that runs all ETL jobs
    run_all_etl = PythonOperator(
        task_id='run_all_smart_city_etl',
        python_callable=run_all_smart_city_jobs,
        doc_md="""
        ### Smart City ETL - Unified Process
        
        This task runs the unified Talend job that:
        - Loads all dimension tables in proper order
        - Loads all fact tables after dimensions
        - Handles dependencies internally
        - Processes: buildings, bus_routes, calendar, devices, event_types, trucks, zones, bus_gps, emergency_calls, energy_consumption, traffic, waste_collection
        """
    )
