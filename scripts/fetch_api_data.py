#!/usr/bin/env python3
"""
fetch_api_data.py
==================

This script queries the CoinGecko API for the top‐N cryptocurrencies ranked by
market capitalisation and writes a CSV snapshot.  Each record contains basic
metrics (price, market cap, volume, rank) and a snapshot date.  Optionally, the
script attempts to enrich each coin with its launch date and category by
calling the `/coins/{id}` endpoint.

Usage:

```
python fetch_api_data.py --top 10 --currency usd --out /tmp/snapshot.csv
```

Environment variables `REQUESTS_TIMEOUT` (seconds) and `COINGECKO_API_URL` can
override defaults.
"""

import argparse
import csv
import datetime
import os
import sys
import time
from typing import Dict, Iterable, Optional

import requests

DEFAULT_API_URL = os.environ.get("COINGECKO_API_URL", "https://api.coingecko.com/api/v3")
DEFAULT_TIMEOUT = float(os.environ.get("REQUESTS_TIMEOUT", "10"))


def fetch_market_data(top: int, currency: str) -> Iterable[Dict[str, object]]:
    """Fetch market data for the top cryptocurrencies from CoinGecko.

    Args:
        top: number of top coins to fetch (by market cap).
        currency: fiat currency (e.g. 'usd', 'eur') for price and market cap.

    Returns:
        An iterable of dictionaries with market metrics.
    """
    url = f"{DEFAULT_API_URL}/coins/markets"
    params = {
        "vs_currency": currency,
        "order": "market_cap_desc",
        "per_page": top,
        "page": 1,
        "sparkline": "false",
        "price_change_percentage": "24h",
    }
    resp = requests.get(url, params=params, timeout=DEFAULT_TIMEOUT)
    resp.raise_for_status()
    data = resp.json()
    snapshot_date = datetime.date.today().isoformat()
    for item in data:
        yield {
            "coin_id": item.get("id"),
            "symbol": item.get("symbol"),
            "name": item.get("name"),
            "price_usd": item.get("current_price"),
            "price_change_percentage_24h": item.get("price_change_percentage_24h"),
            "market_cap_usd": item.get("market_cap"),
            "volume_24h_usd": item.get("total_volume"),
            "market_cap_rank": item.get("market_cap_rank"),
            "snapshot_date": snapshot_date,
        }


def fetch_coin_metadata(coin_id: str) -> Dict[str, Optional[str]]:
    """Fetch metadata (launch date and category) for a specific coin.

    Args:
        coin_id: the CoinGecko identifier for the coin.

    Returns:
        A dictionary with keys 'launch_date' and 'category'.  If metadata is
        unavailable, values will be None or an empty string.
    """
    url = f"{DEFAULT_API_URL}/coins/{coin_id}"
    params = {
        "localization": "false",
        "tickers": "false",
        "market_data": "false",
        "community_data": "false",
        "developer_data": "false",
        "sparkline": "false",
    }
    try:
        resp = requests.get(url, params=params, timeout=DEFAULT_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        genesis_date = data.get("genesis_date")  # e.g. '2017-07-23'
        categories = data.get("categories", []) or []
        category = ", ".join(categories) if categories else ""
        return {
            "launch_date": genesis_date,
            "category": category,
        }
    except Exception:
        # If metadata cannot be retrieved, return defaults
        return {"launch_date": None, "category": ""}


def write_csv(records: Iterable[Dict[str, object]], out_path: str) -> None:
    """Write records to a CSV file.

    Args:
        records: an iterable of dictionaries containing market data.
        out_path: path to output CSV file.
    """
    fieldnames = [
        "coin_id",
        "symbol",
        "name",
        "price_usd",
        "price_change_percentage_24h",
        "market_cap_usd",
        "volume_24h_usd",
        "market_cap_rank",
        "snapshot_date",
    ]
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for rec in records:
            writer.writerow(rec)


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Fetch CoinGecko market data and write to CSV")
    parser.add_argument("--top", type=int, default=10, help="Number of top coins to fetch (default: 10)")
    parser.add_argument("--currency", type=str, default="usd", help="Fiat currency for price/market cap (default: usd)")
    parser.add_argument("--out", type=str, required=True, help="Output CSV file path")
    args = parser.parse_args(argv)

    records = list(fetch_market_data(args.top, args.currency))
    write_csv(records, args.out)
    print(f"Wrote {len(records)} rows to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())