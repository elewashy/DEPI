from __future__ import annotations
import os
from datetime import datetime

from airflow.models.dag import DAG
from airflow.operators.bash import BashOperator

# Path to Talend Jobs folder
TALEND_JOBS_BASE_PATH = "/opt/airflow/dags/Smart_City"

# Get the list of Talend job directories
try:
    job_directories = [
        d
        for d in os.listdir(TALEND_JOBS_BASE_PATH)
        if os.path.isdir(os.path.join(TALEND_JOBS_BASE_PATH, d)) and d != "lib"
    ]
except FileNotFoundError:
    job_directories = []

# Generate a DAG for each Talend job
for job_name in job_directories:
    dag_id = f"talend_{job_name}"

    job_path = os.path.join(TALEND_JOBS_BASE_PATH, job_name)
    script_name = f"{job_name}_run.sh"
    script_path = os.path.join(job_path, script_name)

    # Check that the script exists before we create the DAG.
    if not os.path.isfile(script_path):
        continue

    with DAG(
        dag_id=dag_id,
        start_date=datetime(2023, 1, 1),
        schedule_interval=None,
        catchup=False,
        tags=["talend"],
    ) as dag:

        run_talend_job = BashOperator(
            task_id=f"run_{job_name}",
            bash_command=f"chmod +x '{script_path}' && '{script_path}'",
        )

        globals()[dag_id] = dag
