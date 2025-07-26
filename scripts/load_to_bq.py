#!/usr/bin/env python3
"""
load_to_bq.py
=============

Load a CSV file from Google Cloud Storage into a BigQuery table.  This script
uses the `google-cloud-bigquery` library.  It assumes that the CSV file has a
header row and that BigQuery should autodetect the schema.  The default
behaviour appends rows to the destination table.

Usage:

```
python load_to_bq.py \
  --project my-project \
  --dataset crypto_dw \
  --table crypto_raw_stage \
  --gcs-uri gs://my-bucket/raw/snapshot_2024-01-01.csv
```
"""

import argparse
import sys
from typing import Optional

from google.cloud import bigquery


def load_csv_from_gcs(project: str, dataset: str, table: str, gcs_uri: str) -> None:
    """Load a CSV from GCS into a BigQuery table.

    Args:
        project: GCP project ID.
        dataset: BigQuery dataset ID.
        table: BigQuery table ID (within the dataset).
        gcs_uri: Full GCS URI to the CSV file.
    """
    client = bigquery.Client(project=project)
    table_ref = f"{project}.{dataset}.{table}"
    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.CSV,
        skip_leading_rows=1,
        autodetect=True,
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
    )
    load_job = client.load_table_from_uri(gcs_uri, table_ref, job_config=job_config)
    print(f"Starting load job: {load_job.job_id}")
    load_job.result()  # Wait for job to complete
    print(f"Loaded data into {table_ref} from {gcs_uri}")


def main(argv: Optional[object] = None) -> int:
    parser = argparse.ArgumentParser(description="Load a CSV from GCS into BigQuery")
    parser.add_argument("--project", required=True, help="GCP project ID")
    parser.add_argument("--dataset", required=True, help="BigQuery dataset ID")
    parser.add_argument("--table", required=True, help="BigQuery table ID")
    parser.add_argument("--gcs-uri", required=True, help="GCS URI of the CSV file")
    args = parser.parse_args(argv)
    load_csv_from_gcs(args.project, args.dataset, args.table, args.gcs_uri)
    return 0


if __name__ == "__main__":
    sys.exit(main())