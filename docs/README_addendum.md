# 📎 README Addendum: Implementation Notes & Special Considerations

This document complements the main `README.md` and highlights additional details, edge cases, and implementation tips relevant to the CoinGecko crypto data pipeline project.

---

## 🔍 API & Data Considerations

### CoinGecko API
- The pipeline uses the `/coins/markets` and `/coins/{id}` endpoints.
- Sparkline data is used to calculate **7-day volatility**.
- Rate-limiting may require retries or caching for large-scale deployment.

### Data Types
- Prices, volumes, and market cap values are stored as **NUMERIC** for precision.
- Volatility is computed using **NumPy** (standard deviation).

---

## 💡 Airflow DAG Design

- DAG ID: `crypto_etl_dag`
- Schedule: Daily (can be parameterized for backfilling)
- Uses `PythonOperator` to fetch SQL and `BeamRunPythonPipelineOperator` to run Beam jobs.
- Modular task structure:
  - `fetch_sql`
  - `create_star_schema`
  - `run_fetch_crypto_data`
  - `run_populate_crypto_asset_dim`
  - `run_populate_date_dim`

---

## 📂 GCS Folder Structure

```
gs://your-composer-bucket/
├── dags/
│   ├── crypto_etl_dag.py
│   └── scripts/
│       ├── fetch_crypto_data.py
│       ├── populate_crypto_asset_dim.py
│       └── populate_date_dim.py

gs://your-data-bucket/
├── sql/
│   └── create_tables.sql
├── requirements/
│   └── requirements.txt
├── docs/
│   ├── architecture_diagram_description.md
│   ├── dimensional_model.md
│   └── README_addendum.md
├── configs/
│   └── cloudbuild.yaml
```

---

## 🛡️ Security & Permissions

- The Composer environment must have access to:
  - BigQuery dataset: `crypto_data`
  - GCS buckets for DAGs, scripts, and data output
- The **Cloud Build service account** needs the following roles:
  - `Storage Admin`
  - `Composer Worker`
  - `BigQuery Admin` (optional for table creation)

---

## 📊 Monitoring & Logging

- All DAG task logs are visible via Cloud Composer (Airflow UI)
- Dataflow jobs can be monitored from:
  - Dataflow Console
  - Stackdriver Logging (via Airflow integration)
- Beam logs stderr/stdout directly to Dataflow logs

---

## 🛠️ Troubleshooting Tips

| Issue                        | Solution                                                  |
|-----------------------------|-----------------------------------------------------------|
| DAG not appearing           | Ensure DAG is in Composer bucket under `/dags/`           |
| API failure                 | Add exponential retry logic or fallback cache             |
| CSV shards in GCS           | Set `shard_name_template=''` in Beam `WriteToText`        |
| Dataflow runner errors      | Ensure `apache-beam[gcp]` is installed, and use Python 3  |

---

## 🔮 Future Ideas

- Ingest real-time websocket crypto feed
- Expand to 50–100 coins using pagination
- Use Cloud Functions to trigger DAGs from external events
- Build Looker Studio dashboards on top of BigQuery warehouse