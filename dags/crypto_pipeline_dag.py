from airflow import models
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import PythonOperator
from airflow.providers.google.cloud.operators.bigquery import BigQueryInsertJobOperator
from airflow.providers.apache.beam.operators.beam import BeamRunPythonPipelineOperator, DataflowConfiguration
from airflow.providers.google.cloud.hooks.gcs import GCSHook
from datetime import datetime, timedelta

# Project-specific configurations
PROJECT_ID = 'blockpulse-insights-project'
REGION = 'us-central1'
BUCKET_NAME = 'blockpulse-data-bucket'
TEMP_LOCATION = f'gs://{BUCKET_NAME}/temp/'
STAGING_LOCATION = f'gs://{BUCKET_NAME}/staging/'
ETL_PATH = f'gs://{BUCKET_NAME}/etl/'
SQL_FILE_PATH = 'sql/create_tables.sql'
REQUIREMENTS_FILE = f'{ETL_PATH}requirements.txt'

default_args = {
    'owner': 'you',
    'start_date': datetime(2025, 1, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=2)
}

# Function to fetch SQL from GCS
def get_sql_from_gcs(**kwargs):
    gcs_hook = GCSHook(gcp_conn_id='google_cloud_default')
    file_content = gcs_hook.download_as_byte_array(
        bucket_name=BUCKET_NAME,
        object_name=SQL_FILE_PATH
    ).decode('utf-8')
    return file_content

with models.DAG(
    dag_id='crypto_etl_dag',
    default_args=default_args,
    schedule_interval='@daily',
    catchup=False,
    description='Daily CoinGecko pipeline using Dataflow and BigQuery'
) as dag:

    start = EmptyOperator(task_id='start')

    # Pull SQL from GCS
    fetch_sql = PythonOperator(
        task_id='fetch_sql',
        python_callable=get_sql_from_gcs
    )

    # Create BQ tables
    create_star_schema = BigQueryInsertJobOperator(
        task_id='create_star_schema',
        configuration={
            "query": {
                "query": "{{ task_instance.xcom_pull(task_ids='fetch_sql') }}",
                "useLegacySql": False
            }
        },
        location=REGION,
        project_id=PROJECT_ID
    )

    # Run Python ETL on Dataflow using Beam
    run_crypto_etl = BeamRunPythonPipelineOperator(
        task_id='run_crypto_etl',
        py_file=f"{ETL_PATH}fetch_crypto_data.py",
        requirements_file=REQUIREMENTS_FILE,  # Use requirements.txt instead of py_requirements
        dataflow_config=DataflowConfiguration(
            job_name="{{ 'cryptoetl-' ~ ts_nodash | replace('T', '') | lower }}",
            project_id=PROJECT_ID,
            location=REGION,
            wait_until_finished=True
        ),
        gcp_conn_id='google_cloud_default',
        runner='DataflowRunner',
        pipeline_options={
            "tempLocation": TEMP_LOCATION,
            "stagingLocation": STAGING_LOCATION,
            "project": PROJECT_ID,
            "region": REGION
        },
        py_interpreter='python3',
        py_system_site_packages=False
    )

    end = EmptyOperator(task_id='end')

    start >> fetch_sql >> create_star_schema >> run_crypto_etl >> end
