# BlockPulse Crypto Market Intelligence Pipeline

This repository implements a full end‑to‑end data engineering pipeline for **BlockPulse Insights**, a hypothetical crypto analytics startup.  The goal of the pipeline is to ingest daily snapshots of cryptocurrency market data, transform the raw data into a dimensional model following a star schema and load it into a cloud data warehouse.  The result is a well‑structured, query‑friendly dataset that powers dashboards and advanced analytics.

## Project Overview

Cryptocurrency markets are highly volatile and generate vast amounts of data every day.  Investors, researchers and developers need reliable, up‑to‑date information on prices, trading volumes, market capitalisation and other market metrics.  BlockPulse Insights solves this problem by building an automated, cloud‑native pipeline that fetches market data from public APIs, processes it and stores it in a warehouse for long‑term analysis.  A daily schedule ensures that users always have the most recent data available.

### Key Features

- **Daily ingestion** of top‑N cryptocurrency metrics from the [CoinGecko API](https://www.coingecko.com/), capturing price, market cap, volume, market cap rank and associated metadata.
- **Cloud storage** of raw CSV snapshots in Google Cloud Storage (GCS) as an immutable data lake.
- **Transformations** to prepare clean data and populate a star schema consisting of a fact table (`crypto_market_snapshot_fact`) and two dimension tables (`crypto_asset_dim` and `date_dim`).
- **BigQuery warehouse** partitioned by date for efficient analytical queries and dashboards.
- **Apache Airflow** orchestration (via Google Cloud Composer) to schedule and monitor the daily pipeline.
- **Extensibility**: modular code that supports adding new coins or metrics without major refactoring.

The repository is organised to provide clear separation between the ingestion code, Airflow DAG definitions, SQL DDL scripts and documentation.  A high‑level architecture diagram and dimensional model are provided in the `docs/` folder.

## Repository Structure

```
blockpulse_capstone/
├── dags/                  # Airflow DAG definitions
│   └── crypto_pipeline_dag.py
├── docs/                  # Diagrams and figures used in documentation
│   ├── architecture_diagram.png
│   └── dimensional_model.png
├── scripts/               # Stand‑alone Python scripts for data ingestion
│   ├── fetch_api_data.py
│   ├── load_to_gcs.py
│   └── load_to_bq.py
├── sql/                   # SQL scripts to create tables and stored procedures
│   ├── create_tables.sql
│   ├── sp_upsert_crypto_asset_dim.sql
│   └── sp_upsert_date_dim.sql
└── README.md              # You are here
```

### `dags/`

Contains the Airflow DAG definition (`crypto_pipeline_dag.py`).  The DAG orchestrates the pipeline by running tasks in the following order:

1. **Start** – logs the start of the run.
2. **Fetch and upload raw data** – calls a Python function to query the CoinGecko API for the top‑N coins and upload the resulting CSV to GCS.
3. **Load to BigQuery (raw stage)** – loads the CSV snapshot into an external/temporary table in BigQuery.
4. **Transform and load dimension tables** – calls stored procedures to upsert records into `crypto_asset_dim` and `date_dim`.
5. **Transform and load fact table** – inserts the daily metrics into `crypto_market_snapshot_fact` using data from the raw table and dimension keys.
6. **End** – logs completion.

### `scripts/`

Individual Python scripts encapsulate pieces of functionality so they can be reused outside of Airflow if needed:

- **`fetch_api_data.py`** – fetches JSON data from the CoinGecko API, normalises it into a pandas DataFrame and writes a CSV file.  The script supports specifying the number of coins, target currency and output file path.
- **`load_to_gcs.py`** – uploads a local file to a specified GCS bucket and path.
- **`load_to_bq.py`** – creates an external table in BigQuery pointing at a CSV in GCS or loads data into a staging table.  It is used by the DAG to load raw snapshots.

### `sql/`

DDL and stored procedure scripts for BigQuery.  The repository includes:

- **`create_tables.sql`** – creates the fact and dimension tables following the star schema defined below.  It also creates a staging table for raw data.
- **`sp_upsert_crypto_asset_dim.sql`** – stored procedure to upsert records into the `crypto_asset_dim` dimension using the latest raw snapshot.
- **`sp_upsert_date_dim.sql`** – stored procedure to upsert dates into the `date_dim` dimension.

## Dimensional Model

The star schema is designed around a fact table capturing daily metrics for each cryptocurrency and two dimension tables.  The fact table is partitioned by `snapshot_date` to support efficient time‑series queries.

### Tables

| Table                     | Description                                                                               |
|---------------------------|-------------------------------------------------------------------------------------------|
| `crypto_asset_dim`        | Unique list of cryptocurrencies with natural key (`coin_id`), symbol, name, category and launch date.  A surrogate key (`asset_key`) is used as the foreign key in the fact table. |
| `date_dim`                | Standard calendar attributes for each date (year, month, day, quarter, week, day_of_week, etc.).  The surrogate key (`date_key`) is used in the fact table. |
| `crypto_market_snapshot_fact` | Fact table capturing daily metrics per coin: price in USD, market cap in USD, 24h trading volume in USD, market cap rank, daily price change percentage and any other derived metrics.  Contains foreign keys `date_key` and `asset_key`. |
| `crypto_raw_stage`        | A staging table for loading raw JSON/CSV snapshots from the API before transformations. |

See `docs/dimensional_model.png` for an illustration of the star schema.

## Architecture

The pipeline leverages Google Cloud services for scalability and reliability.  An overview of the architecture is shown in the diagram below (also available in `docs/architecture_diagram.png`).

1. **CoinGecko API** – Provides real‑time market data for cryptocurrencies.
2. **Cloud Composer (Airflow)** – Orchestrates the daily workflow via a DAG.
3. **Cloud Storage** – Stores raw CSV snapshots uploaded by the pipeline.
4. **BigQuery** – Acts as the data warehouse, with separate staging, dimension and fact tables.  Stored procedures manage dimension upserts.
5. **Visualization layer (Looker/Data Studio)** – Consumes the fact/dimension tables for dashboards and ad‑hoc analysis.

## Getting Started

Follow these steps to set up and run the BlockPulse pipeline in your own GCP environment.  You will need a GCP project with billing enabled and appropriate IAM permissions.

### 1. Create GCS Bucket and BigQuery Dataset

1. Create a **Google Cloud Storage** bucket to store the raw CSV snapshots.  Ensure the service account used by Cloud Composer has read/write access to the bucket.
2. Create a **BigQuery dataset** (e.g., `crypto_dw`) in the same project and region as your Cloud Composer environment.
3. Assign the following IAM roles to the service account used by Cloud Composer:
   - `roles/storage.objectAdmin` on the GCS bucket.
   - `roles/bigquery.dataEditor` on the BigQuery dataset.

### 2. Deploy the BigQuery Tables and Stored Procedures

Run the SQL scripts in the `sql/` folder to create the tables and stored procedures:

```bash
# From the root of the repository
export PROJECT_ID=<your-project-id>
export DATASET=crypto_dw

bq query --use_legacy_sql=false --project_id=$PROJECT_ID < sql/create_tables.sql
bq query --use_legacy_sql=false --project_id=$PROJECT_ID < sql/sp_upsert_crypto_asset_dim.sql
bq query --use_legacy_sql=false --project_id=$PROJECT_ID < sql/sp_upsert_date_dim.sql
```

These scripts will create the staging table (`crypto_raw_stage`), the dimension tables (`crypto_asset_dim`, `date_dim`), the fact table (`crypto_market_snapshot_fact`) and the stored procedures used in the pipeline.

### 3. Deploy the Airflow DAG

1. Create or identify an existing **Cloud Composer** environment in your project.
2. Copy the contents of the `dags/` directory into the environment’s DAGs folder (e.g., `gs://<composer-bucket>/dags/`).
3. Copy the `scripts/` directory into the environment’s `data/` folder or another suitable location in your Composer bucket so the DAG can import the modules.
4. In the Airflow UI, you should see a DAG named `crypto_market_pipeline`.  Turn it on.  The DAG is configured to run daily at 00:00 UTC.

### 4. Configure the DAG

The DAG uses Airflow variables to determine runtime behaviour:

- `project_id` – your GCP project ID.
- `bq_dataset` – the BigQuery dataset used (default: `crypto_dw`).
- `gcs_bucket` – name of the GCS bucket for raw snapshots.
- `top_n` – number of top cryptocurrencies to fetch (default: 10).
- `currency` – the fiat currency to fetch metrics in (default: `usd`).

Set these variables in the Airflow UI under **Admin → Variables** or define them in the DAG file.

### 5. Run and Monitor

Once deployed and configured, the DAG will run automatically on schedule.  You can trigger a backfill for historical dates by adjusting the `start_date` in the DAG.  Use Airflow’s **Tree View** and **Task Instance Details** to monitor each step.  BigQuery’s query history will show the effect of stored procedure calls.

### 6. Visualise the Data

With the data loaded into the star schema, you can create dashboards in **Looker**, **Data Studio** or any BI tool that supports BigQuery.  Join the fact table to the dimension tables on `asset_key` and `date_key` to analyse price trends, market capitalisation and trading volumes over time.  Example queries are included in the comments of the `create_tables.sql` script.

## Extending the Pipeline

To adapt the pipeline for additional currencies, metrics or a different cloud provider:

- **Additional metrics or currencies** – Modify `fetch_api_data.py` to include extra fields from the CoinGecko API or call different endpoints.  Update the BigQuery schema accordingly and adjust the transformation logic in the DAG.
- **New dimension tables** – For example, you could add a `currency_dim` if you ingest data in multiple fiat currencies.
- **Azure implementation** – Replace Cloud Composer with Azure Data Factory and BigQuery with Azure Synapse Analytics or Databricks.  The modular structure of the repository allows you to swap out the storage/compute layers while keeping the core ETL logic.

## License

This project is provided under the MIT License.  See the [LICENSE](../LICENSE) file for details.