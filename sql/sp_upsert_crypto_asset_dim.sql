-- Stored procedure to upsert new cryptocurrency assets into the dimension table.
-- Replace `{{ dataset }}` with your BigQuery dataset name before executing.

CREATE OR REPLACE PROCEDURE `crypto_dw.sp_upsert_crypto_asset_dim`()
BEGIN
  DECLARE max_key INT64;
  -- Determine current maximum surrogate key
  SET max_key = COALESCE((SELECT MAX(asset_key) FROM `crypto_dw.crypto_asset_dim`), 0);
  -- Insert new assets not already present in the dimension table
  INSERT INTO `crypto_dw.crypto_asset_dim` (asset_key, coin_id, symbol, name, category, launch_date)
  SELECT
    max_key + ROW_NUMBER() OVER() AS asset_key,
    r.coin_id,
    r.symbol,
    r.name,
    '' AS category,
    CAST(NULL AS DATE) AS launch_date
  FROM (
    SELECT DISTINCT coin_id, symbol, name
    FROM `crypto_dw.crypto_raw_stage`
  ) AS r
  LEFT JOIN `crypto_dw.crypto_asset_dim` AS d
    ON d.coin_id = r.coin_id
  WHERE d.coin_id IS NULL;
END;
