# 🚀 CoinGecko Crypto Data Pipeline (GCP + Apache Beam + BigQuery)

This project implements a fully cloud-native ETL pipeline that fetches cryptocurrency market data from the [CoinGecko API](https://www.coingecko.com/), processes it using **Apache Beam**, stores it in **Google Cloud Storage**, and loads it into a **BigQuery data warehouse** following a **star schema**.

---

## 📦 Project Structure

```
coingecko-pipeline/
├── dags/                         # Airflow DAGs
│   └── crypto_etl_dag.py
├── scripts/                      # Beam-compatible ETL scripts
│   ├── fetch_crypto_data.py
│   ├── populate_crypto_asset_dim.py
│   └── populate_date_dim.py
├── sql/                          # BigQuery schema setup
│   └── create_tables.sql
├── docs/                         # Project artifacts and documentation
│   ├── dimensional_model.md
│   ├── architecture_diagram_description.md
│   └── README_addendum.md
├── requirements.txt              # Python dependencies
├── cloudbuild.yaml               # GCP CI/CD pipeline
└── README.md                     # Project overview
```

---

## 📊 Star Schema Overview

**Fact Table**
- `crypto_market_snapshot_fact`: Daily metrics per coin (price, volume, market cap, volatility)

**Dimension Tables**
- `crypto_asset_dim`: Coin metadata (name, symbol, category, launch date)
- `date_dim`: Calendar table for BI reporting

---

## ⚙️ Tools & Services Used

| Component       | Technology                |
|----------------|----------------------------|
| API Source      | CoinGecko REST API         |
| Data Processing | Apache Beam (Python)       |
| Orchestration   | Cloud Composer (Airflow)   |
| Data Storage    | Google Cloud Storage       |
| Data Warehouse  | BigQuery                   |
| CI/CD           | Cloud Build + GitHub       |

---

## 🔁 Pipeline Workflow

1. DAG is triggered daily via Cloud Composer
2. SQL schema is read from GCS and used to initialize BigQuery tables
3. Beam jobs are executed on **Dataflow**:
    - `fetch_crypto_data.py`: Coin metrics → GCS → BigQuery
    - `populate_crypto_asset_dim.py`: Coin metadata → GCS → BigQuery
    - `populate_date_dim.py`: Date records → GCS → BigQuery

---

## 🚀 Deployment Steps

1. **Set up GCS Buckets**
   - `your-composer-bucket` (for DAGs)
   - `your-data-bucket` (for SQL, docs, outputs)

2. **Create BigQuery Dataset**
   ```sql
   CREATE SCHEMA `your-project-id.crypto_data`;
   ```

3. **Run Cloud Build via Trigger**
   - Trigger on GitHub push using `cloudbuild.yaml`
   - This will upload:
     - DAGs → `gs://your-composer-bucket/dags/`
     - Scripts → `gs://your-composer-bucket/dags/scripts/`
     - SQL → `gs://your-data-bucket/sql/`
     - Docs and config → appropriate folders

4. **Monitor DAG in Composer UI**
   - View tasks and logs
   - Ensure success on daily runs

---

## 📁 Required Permissions

- Cloud Build service account:
  - `Storage Admin`
  - `Composer Worker`
- Composer environment should have:
  - Apache Beam SDK installed
  - Access to `gsutil` and BigQuery

---

## 🛠️ Optimization Tips

- Enable BigQuery table partitioning and clustering
- Monitor Dataflow pipeline cost and auto-scaling
- Use caching for API rate-limited endpoints

---

## 🙌 Authors

- Developed by [Your Name]
- Inspired by best practices from [10Alytics Capstone](https://10alytics.com)

---

## 📄 License

This project is licensed under the MIT License. Feel free to adapt and extend for your own use.