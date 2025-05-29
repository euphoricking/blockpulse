-- FACT TABLE: Daily market snapshot per asset
CREATE TABLE IF NOT EXISTS `blockpulse-insights-project.crypto_data.crypto_market_snapshot_fact` (
  `snapshot_date` DATE,
  `asset_id` STRING,
  `name` STRING,
  `symbol` STRING,
  `current_price` NUMERIC,
  `market_cap` NUMERIC,
  `total_volume` NUMERIC,
  `volatility` NUMERIC
)
PARTITION BY snapshot_date
OPTIONS(
  description = "Fact table capturing daily market metrics per crypto asset"
);

-- DIMENSION TABLE: Asset metadata
CREATE TABLE IF NOT EXISTS `blockpulse-insights-project.crypto_data.crypto_asset_dim` (
  `asset_id` STRING,
  `name` STRING,
  `symbol` STRING,
  `launch_date` DATE,
  `category` STRING
)
OPTIONS(
  description = "Dimension table for crypto asset metadata"
);

-- DIMENSION TABLE: Calendar dimension
CREATE TABLE IF NOT EXISTS `blockpulse-insights-project.crypto_data.date_dim` (
  `date` DATE,
  `year` INT64,
  `month` INT64,
  `day` INT64,
  `day_of_week` STRING
)
OPTIONS(
  description = "Calendar dimension table to support time-based analysis"
);
