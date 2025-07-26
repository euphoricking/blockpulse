"""
crypto_pipeline_dag.py
======================

Airflow DAG to orchestrate the BlockPulse crypto market data pipeline.  The DAG
runs daily and performs the following steps:

1. Fetch market data from the CoinGecko API for the top‑N coins and write a
   CSV snapshot to a local temporary file.
2. Upload the snapshot to a specified GCS bucket.
3. Load the CSV into a staging table in BigQuery.
4. Upsert any new coins into the crypto_asset_dim and new dates into the
   date_dim using stored procedures.
5. Insert the day's metrics into the fact table using foreign keys from the
   dimension tables.

Airflow Variables
-----------------

The DAG reads a number of variables at runtime.  Set these in the Airflow UI
under **Admin → Variables** or edit the defaults in this file.

- `project_id`: GCP project ID
- `bq_dataset`: BigQuery dataset ID (default: `crypto_dw`)
- `gcs_bucket`: GCS bucket name for raw snapshots
- `top_n`: number of coins to fetch (default: 10)
- `currency`: fiat currency code (default: `usd`)

Service Account Permissions
--------------------------

The service account associated with the Airflow workers needs access to the
CoinGecko API (outbound internet), read/write permissions to the GCS bucket
(`roles/storage.objectAdmin`) and BigQuery Data Editor privileges on the
dataset (`roles/bigquery.dataEditor`).
"""

import datetime
import os

from airflow import DAG
from airflow.models import Variable
from airflow.operators.dummy import DummyOperator
from airflow.operators.python import PythonOperator

# Import helper functions from the scripts directory.  These modules must be
# available on the Airflow workers' PYTHONPATH.  In Cloud Composer you can
# upload the `scripts` directory to the environment bucket and add it to
# `PYTHONPATH` via the `plugins.zip` or the `composer.json` mechanism.
from blockpulse_capstone.scripts.fetch_api_data import fetch_market_data, write_csv
from blockpulse_capstone.scripts.load_to_gcs import upload_file
from blockpulse_capstone.scripts.load_to_bq import load_csv_from_gcs

try:
    from google.cloud import bigquery
except ImportError:
    # Allow DAG to be parsed even if the BigQuery client is unavailable at parse time.
    bigquery = None


def fetch_and_upload_data(**context) -> None:
    """Fetch market data and upload the CSV snapshot to GCS.

    The function uses Airflow Variables to determine runtime parameters.  It
    writes the snapshot to a temporary file, uploads it to the configured
    bucket and pushes the resulting GCS URI to XCom for downstream tasks.
    """
    project_id = Variable.get("project_id")
    dataset = Variable.get("bq_dataset", default_var="crypto_dw")
    bucket = Variable.get("gcs_bucket")
    top_n = int(Variable.get("top_n", default_var="10"))
    currency = Variable.get("currency", default_var="usd")

    # Generate a temporary file path
    tmp_dir = "/tmp"
    date_str = datetime.date.today().isoformat()
    file_name = f"crypto_snapshot_{date_str}.csv"
    local_path = os.path.join(tmp_dir, file_name)

    # Fetch data and write to CSV
    records = list(fetch_market_data(top_n, currency))
    write_csv(records, local_path)

    # Upload to GCS
    dest_blob_name = f"raw/{file_name}"
    upload_file(bucket, local_path, dest_blob_name)

    gcs_uri = f"gs://{bucket}/{dest_blob_name}"
    # Push the GCS URI to XCom for the next task
    context["ti"].xcom_push(key="gcs_uri", value=gcs_uri)


def load_raw_stage(**context) -> None:
    """Load the raw CSV from GCS into the staging table in BigQuery."""
    project_id = Variable.get("project_id")
    dataset = Variable.get("bq_dataset", default_var="crypto_dw")
    table = "crypto_raw_stage"
    gcs_uri = context["ti"].xcom_pull(key="gcs_uri")
    load_csv_from_gcs(project_id, dataset, table, gcs_uri)


def upsert_dimensions(**context) -> None:
    """Call stored procedures to update the asset and date dimensions."""
    project_id = Variable.get("project_id")
    dataset = Variable.get("bq_dataset", default_var="crypto_dw")
    if bigquery is None:
        raise RuntimeError("google-cloud-bigquery is not available on the Airflow worker")
    client = bigquery.Client(project=project_id)
    # Upsert asset dimension
    client.query(f"CALL `{dataset}.sp_upsert_crypto_asset_dim`();").result()
    # Upsert date dimension
    client.query(f"CALL `{dataset}.sp_upsert_date_dim`();").result()


def load_fact_table(**context) -> None:
    """Insert the day's snapshot into the fact table, resolving foreign keys."""
    project_id = Variable.get("project_id")
    dataset = Variable.get("bq_dataset", default_var="crypto_dw")
    date_str = datetime.date.today().isoformat()
    if bigquery is None:
        raise RuntimeError("google-cloud-bigquery is not available on the Airflow worker")
    client = bigquery.Client(project=project_id)
    sql = f"""
    INSERT INTO `{project_id}.{dataset}.crypto_market_snapshot_fact`
      (date_key, asset_key, price_usd, price_change_percentage_24h, market_cap_usd, volume_24h_usd, market_cap_rank, snapshot_date)
    SELECT
      d.date_key,
      a.asset_key,
      r.price_usd,
      r.price_change_percentage_24h,
      r.market_cap_usd,
      r.volume_24h_usd,
      r.market_cap_rank,
      r.snapshot_date
    FROM `{project_id}.{dataset}.crypto_raw_stage` AS r
    JOIN `{project_id}.{dataset}.crypto_asset_dim` AS a ON a.coin_id = r.coin_id
    JOIN `{project_id}.{dataset}.date_dim` AS d ON d.date = r.snapshot_date
    WHERE r.snapshot_date = DATE(@run_date);
    """
    # Bind run_date parameter to ensure idempotence
    job_config = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("run_date", "DATE", datetime.date.today())]
    )
    client.query(sql, job_config=job_config).result()


default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "email_on_failure": True,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": datetime.timedelta(minutes=5),
}

with DAG(
    dag_id="crypto_market_pipeline",
    default_args=default_args,
    description="Daily crypto market data pipeline for BlockPulse",
    schedule_interval="0 0 * * *",
    start_date=datetime.datetime(2024, 1, 1),
    catchup=False,
    tags=["crypto", "blockpulse", "data-engineering"],
) as dag:
    start = DummyOperator(task_id="start")
    fetch_upload = PythonOperator(
        task_id="fetch_and_upload",
        python_callable=fetch_and_upload_data,
        provide_context=True,
    )
    load_raw = PythonOperator(
        task_id="load_raw_stage",
        python_callable=load_raw_stage,
        provide_context=True,
    )
    upsert_dims = PythonOperator(
        task_id="upsert_dimensions",
        python_callable=upsert_dimensions,
        provide_context=True,
    )
    load_fact = PythonOperator(
        task_id="load_fact_table",
        python_callable=load_fact_table,
        provide_context=True,
    )
    end = DummyOperator(task_id="end")

    start >> fetch_upload >> load_raw >> upsert_dims >> load_fact >> end