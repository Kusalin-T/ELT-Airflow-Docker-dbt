from datetime import datetime
from airflow import DAG
from docker.types import Mount
from airflow.operators.python_operator import PythonOperator
# from airflow.utils.dates import days_ago
# from airflow.providers.airbyte.operators.airbyte import AirbyteTriggerSyncOperator
from airflow.providers.docker.operators.docker import DockerOperator
import subprocess

CONN_ID = ''

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False
}

def run_elt_script():
    script_path = "/opt/airflow/elt/elt_script.py"
    result = subprocess.run(["python", script_path],
                            capture_output=True, text=True)
    if result.returncode != 0:
        Exception(f"Script failed with error: {result.stderr}")
    else:
        print(result.stdout)

dag = DAG(
    'elt_and_dbt',
    default_args=default_args,
    description='An ELT workflow with dbt',
    start_date=datetime(2024,8,4),
    catchup=False
)   

t1 = PythonOperator(
    task_id="run_elt_script",
    python_callable=run_elt_script,
    dag=dag
)

# t1 = AirbyteTriggerSyncOperator(
#     task_id="airbyte_postgres_postgres",
#     airbyte_conn_id='airbyte',
#     connection_id=CONN_ID,
#     asynchronous=False,
#     timeout=3600,
#     wait_seconds=3,
#     dag=dag
# )


t2 = DockerOperator(
    task_id="dbt_run",
    image='ghcr.io/dbt-labs/dbt-postgres:1.4.7',
    command = [
        "run",
        "--profiles-dir",
        "/root",
        "--project-dir",
        "/opt/dbt",
        "--full-refresh"
      ],
      auto_remove=True,
      docker_url="unix://var/run/docker.sock",
      network_mode="bridge",
      mounts=[
          Mount(source='C:\\Users\\Buta\\dev\\ELT-Beginner\\custom_postgres',
                target='/opt/dbt', type='bind'),      
          Mount(source='C:\\Users\\Buta\\.dbt',
                target='/root', type='bind')
      ],
      dag=dag
)

t1 >> t2