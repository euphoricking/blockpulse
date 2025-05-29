# 🏗️ Cloud-Native Architecture: CoinGecko Crypto Data Pipeline

This document describes the cloud-native architecture implemented for the CoinGecko crypto data pipeline. It uses **Google Cloud Platform (GCP)** services to orchestrate and process real-time cryptocurrency market data in a scalable, production-grade environment.

---

## 🌐 Overview

The pipeline ingests data from the CoinGecko API, processes it using **Apache Beam on Cloud Dataflow**, and stores the transformed outputs in **Google Cloud Storage** and **BigQuery**, orchestrated by **Cloud Composer (Airflow)**.

---

## 📉 High-Level Architecture Components

```
GitHub → Cloud Build → GCS
                     ↓
                 Cloud Composer (Airflow DAG)
                     ↓
    ┌────────────────────────────────────────┐
    │            Dataflow Pipelines          │
    │ ┌────────────────────────────────────┐ │
    │ │  fetch_crypto_data.py              │ │
    │ │  populate_crypto_asset_dim.py      │ │
    │ │  populate_date_dim.py              │ │
    │ └────────────────────────────────────┘ │
    └────────────────────────────────────────┘
                     ↓
     ┌──────────── GCS Outputs ─────────────┐
     │ crypto_<date>.csv                    │
     │ asset_dim.csv                        │
     │ date_dim.csv                         │
     └──────────────────────────────────────┘
                     ↓
                BigQuery Tables
    - crypto_market_snapshot_fact
    - crypto_asset_dim
    - date_dim
```

---

## ⚙️ Component Breakdown

### 1. **GitHub + Cloud Build**
- Version control and CI/CD automation
- Triggers Cloud Build on every push to `main`
- Uploads: DAGs, scripts, SQL, config files to GCS

### 2. **Cloud Storage (GCS)**
- Stores ETL scripts, DAGs, SQL schema, outputs
- Acts as staging and temp location for Beam jobs

### 3. **Cloud Composer (Airflow)**
- Orchestrates the ETL pipeline with scheduled DAGs
- Invokes Dataflow jobs
- Loads data to BigQuery

### 4. **Dataflow (Apache Beam)**
- Executes Beam pipelines
- Reads → transforms → writes data to GCS
- Python SDK with `BeamRunPythonPipelineOperator`

### 5. **BigQuery**
- Stores cleaned and structured data
- Star schema: 1 fact table + 2 dimension tables
- Ready for analytics, BI tools, Looker, etc.

---

## 📌 Deployment Highlights

- Data is partitioned and written daily
- Modular, scalable, and cost-efficient
- Production-grade logging and error handling
- Easily extensible for more coins or categories

---

## 🧠 Notes

- Composer uses default service account with access to GCS & BQ
- All Beam scripts are Python 3 and DataflowRunner compatible
- DAGs follow a start → task → end structure using `EmptyOperator`

---

## 📎 Optional Enhancements

- Add Looker Studio dashboard
- Integrate alerts for DAG/task failures
- Add rate-limiting cache for CoinGecko API