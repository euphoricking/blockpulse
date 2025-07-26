-- Stored procedure to upsert new dates into the date dimension.
-- Replace `{{ dataset }}` with your BigQuery dataset name before executing.

CREATE OR REPLACE PROCEDURE `crypto_dw.sp_upsert_date_dim`()
BEGIN
  DECLARE max_key INT64;
  -- Determine current maximum date key
  SET max_key = COALESCE((SELECT MAX(date_key) FROM `crypto_dw.date_dim`), 0);
  -- Insert new dates not already present in the dimension
  INSERT INTO `crypto_dw.date_dim` (
    date_key,
    date,
    year,
    quarter,
    month,
    day,
    day_of_week,
    week,
    is_weekend
  )
  SELECT
    max_key + ROW_NUMBER() OVER() AS date_key,
    r.snapshot_date AS date,
    EXTRACT(YEAR FROM r.snapshot_date) AS year,
    EXTRACT(QUARTER FROM r.snapshot_date) AS quarter,
    EXTRACT(MONTH FROM r.snapshot_date) AS month,
    EXTRACT(DAY FROM r.snapshot_date) AS day,
    EXTRACT(DAYOFWEEK FROM r.snapshot_date) AS day_of_week,
    EXTRACT(WEEK FROM r.snapshot_date) AS week,
    CASE WHEN EXTRACT(DAYOFWEEK FROM r.snapshot_date) IN (1, 7) THEN TRUE ELSE FALSE END AS is_weekend
  FROM (
    SELECT DISTINCT snapshot_date
    FROM `crypto_dw.crypto_raw_stage`
  ) AS r
  LEFT JOIN `crypto_dw.date_dim` AS d
    ON d.date = r.snapshot_date
  WHERE d.date IS NULL;
END;