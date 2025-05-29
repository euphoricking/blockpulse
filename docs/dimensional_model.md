# 📊 Dimensional Model: CoinGecko Crypto Data Pipeline

This document outlines the dimensional model for the CoinGecko crypto data pipeline. The schema is designed using the **star schema** approach for optimized analytical queries in **BigQuery**.

---

## 🌟 Star Schema Overview

```
                     +-------------------+
                     |   date_dim        |
                     |-------------------|
                     | date (PK)         |
                     | year              |
                     | month             |
                     | day               |
                     | day_of_week       |
                     +-------------------+
                             ↑
                             |
+-------------------+        |
| crypto_asset_dim  |        |
|-------------------|        |
| asset_id (PK)     |        |
| name              |        |
| symbol            |        |
| launch_date       |        |
| category          |        |
+-------------------+        |
         ↑                   |
         |                   |
         +-------------------+
                   |
                   ↓
      +-------------------------------+
      | crypto_market_snapshot_fact  |
      |-------------------------------|
      | snapshot_date (FK)            |
      | asset_id (FK)                 |
      | name                          |
      | symbol                        |
      | current_price                 |
      | market_cap                    |
      | total_volume                  |
      | volatility                    |
      +-------------------------------+
```

---

## 🧾 Table Descriptions

### 🔹 `crypto_market_snapshot_fact` (Fact Table)
Stores daily market metrics for each crypto asset.

| Column         | Type     | Description                              |
|----------------|----------|------------------------------------------|
| snapshot_date  | DATE     | Date of the snapshot                     |
| asset_id       | STRING   | Foreign key to `crypto_asset_dim`        |
| name           | STRING   | Asset name                               |
| symbol         | STRING   | Asset symbol                             |
| current_price  | NUMERIC  | Latest price in USD                      |
| market_cap     | NUMERIC  | Market capitalization in USD             |
| total_volume   | NUMERIC  | 24h trading volume in USD                |
| volatility     | NUMERIC  | Std. deviation of sparkline over 7 days |

---

### 🔹 `crypto_asset_dim` (Dimension Table)
Contains metadata for each crypto asset.

| Column      | Type    | Description                  |
|-------------|---------|------------------------------|
| asset_id    | STRING  | Unique ID from CoinGecko     |
| name        | STRING  | Full name of the asset       |
| symbol      | STRING  | Abbreviated symbol (e.g., BTC)|
| launch_date | DATE    | Blockchain launch date       |
| category    | STRING  | General asset classification |

---

### 🔹 `date_dim` (Dimension Table)
Standard calendar dimension for time-based filtering and grouping.

| Column       | Type    | Description              |
|--------------|---------|--------------------------|
| date         | DATE    | Calendar date (PK)       |
| year         | INT64   | Year                     |
| month        | INT64   | Month number             |
| day          | INT64   | Day number               |
| day_of_week  | STRING  | Day name (e.g., Monday)  |

---

## 🧠 Design Rationale

- **Star schema** simplifies queries and joins for reporting.
- Allows **partitioning** by date for efficient BigQuery scans.
- All metrics are normalized, timestamped, and scalable.

---

## ✅ Future Enhancements

- Add more dimensions: exchange_dim, blockchain_dim
- Integrate historical CoinGecko OHLCV data
- Add user interaction fact (if personalized tracking is needed)