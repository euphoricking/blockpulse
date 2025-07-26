#!/usr/bin/env python3
"""
load_to_gcs.py
==============

Upload a local file to a specified path in a Google Cloud Storage bucket.  This
script relies on the `google-cloud-storage` library.  Ensure that the
environment variable `GOOGLE_APPLICATION_CREDENTIALS` points to a valid
service‑account JSON key before running.

Usage:

```
python load_to_gcs.py --bucket my-bucket --source /tmp/snapshot.csv --dest raw/snapshot_2024-01-01.csv
```
"""

import argparse
import os
import sys
from typing import Optional

from google.cloud import storage


def upload_file(bucket_name: str, source_file_path: str, destination_blob_name: str) -> None:
    """Upload a file to a GCS bucket.

    Args:
        bucket_name: name of the destination GCS bucket.
        source_file_path: local path to file.
        destination_blob_name: desired object name in the bucket.
    """
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(source_file_path)
    print(f"Uploaded {source_file_path} to gs://{bucket_name}/{destination_blob_name}")


def main(argv: Optional[object] = None) -> int:
    parser = argparse.ArgumentParser(description="Upload a file to Google Cloud Storage")
    parser.add_argument("--bucket", required=True, help="Name of the GCS bucket")
    parser.add_argument("--source", required=True, help="Local file to upload")
    parser.add_argument("--dest", required=True, help="Destination path in the bucket")
    args = parser.parse_args(argv)
    upload_file(args.bucket, args.source, args.dest)
    return 0


if __name__ == "__main__":
    sys.exit(main())