-- Replace `{{ dataset }}` with your BigQuery dataset name before running this script.

-- Staging table for raw snapshots
CREATE TABLE IF NOT EXISTS `crypto_dw.crypto_raw_stage` (
  coin_id STRING,
  symbol STRING,
  name STRING,
  price_usd FLOAT64,
  price_change_percentage_24h FLOAT64,
  market_cap_usd FLOAT64,
  volume_24h_usd FLOAT64,
  market_cap_rank INT64,
  snapshot_date DATE
) PARTITION BY snapshot_date;

-- Dimension table: list of cryptocurrencies.  Surrogate key asset_key will be populated by stored procedure.
CREATE TABLE IF NOT EXISTS `crypto_dw.crypto_asset_dim` (
  asset_key INT64 NOT NULL,
  coin_id STRING NOT NULL,
  symbol STRING,
  name STRING,
  category STRING,
  launch_date DATE,
  insert_ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);

-- Dimension table: calendar dates.  Surrogate key date_key will be populated by stored procedure.
CREATE TABLE IF NOT EXISTS `crypto_dw.date_dim` (
  date_key INT64 NOT NULL,
  date DATE NOT NULL,
  year INT64,
  quarter INT64,
  month INT64,
  day INT64,
  day_of_week INT64,
  week INT64,
  is_weekend BOOL,
  insert_ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);

-- Fact table capturing daily snapshot metrics.
CREATE TABLE IF NOT EXISTS `crypto_dw.crypto_market_snapshot_fact` (
  date_key INT64 NOT NULL,
  asset_key INT64 NOT NULL,
  price_usd FLOAT64,
  price_change_percentage_24h FLOAT64,
  market_cap_usd FLOAT64,
  volume_24h_usd FLOAT64,
  market_cap_rank INT64,
  snapshot_date DATE NOT NULL,
  insert_ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
) PARTITION BY snapshot_date;