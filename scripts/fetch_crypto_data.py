import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
from datetime import datetime, timezone
import requests
import logging

class FetchCryptoMarketSnapshot(beam.DoFn):
    def process(self, element):
        url = 'https://api.coingecko.com/api/v3/coins/markets'
        params = {
            'vs_currency': 'usd',
            'order': 'market_cap_desc',
            'per_page': 10,
            'page': 1,
            'sparkline': False
        }

        logging.info("Sending request to CoinGecko API...")

        try:
            response = requests.get(url, params=params, timeout=60)
            logging.info(f"Response status: {response.status_code}")
            response.raise_for_status()
            data = response.json()

            current_date = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
            logging.info(f"Fetched {len(data)} records")

            for record in data:
                row = {
                    'coin_id': str(record.get('id')),
                    'symbol': str(record.get('symbol')),
                    'name': str(record.get('name')),
                    'price': float(record.get('current_price', 0)),
                    'market_cap': float(record.get('market_cap', 0)),
                    'total_volume': float(record.get('total_volume', 0)),
                    'price_change_percentage_24h': float(record.get('price_change_percentage_24h', 0)),
                    'market_cap_change_percentage_24h': float(record.get('market_cap_change_percentage_24h', 0)),
                    'high_24h': float(record.get('high_24h', 0)),
                    'low_24h': float(record.get('low_24h', 0)),
                    'circulating_supply': float(record.get('circulating_supply', 0)),
                    'total_supply': float(record.get('total_supply', 0)),
                    'max_supply': float(record.get('max_supply', 0)),
                    'ath': float(record.get('ath', 0)),
                    'ath_date': str(record.get('ath_date', '')),
                    'atl': float(record.get('atl', 0)),
                    'atl_date': str(record.get('atl_date', '')),
                    'snapshot_date': current_date,
                    'processing_time': current_date
                }
                logging.info(f"Yielding record for coin: {row['name']}")
                yield row

        except Exception as e:
            logging.error(f"Error fetching data: {str(e)}")
            raise


def run():
    options = PipelineOptions(
        runner='DataflowRunner',
        project='blockpulse-insights-project',
        region='us-central1',
        temp_location='gs://blockpulse-data-bucket/temp/',
        staging_location='gs://blockpulse-data-bucket/staging/',
        setup_file='./setup.py',  # Will be bundled during submission
        save_main_session=True
    )

    output_table = 'blockpulse-insights-project.crypto_data.crypto_market_snapshot_fact'

    schema = {
        "fields": [
            {"name": "coin_id", "type": "STRING"},
            {"name": "symbol", "type": "STRING"},
            {"name": "name", "type": "STRING"},
            {"name": "price", "type": "FLOAT"},
            {"name": "market_cap", "type": "FLOAT"},
            {"name": "total_volume", "type": "FLOAT"},
            {"name": "price_change_percentage_24h", "type": "FLOAT"},
            {"name": "market_cap_change_percentage_24h", "type": "FLOAT"},
            {"name": "high_24h", "type": "FLOAT"},
            {"name": "low_24h", "type": "FLOAT"},
            {"name": "circulating_supply", "type": "FLOAT"},
            {"name": "total_supply", "type": "FLOAT"},
            {"name": "max_supply", "type": "FLOAT"},
            {"name": "ath", "type": "FLOAT"},
            {"name": "ath_date", "type": "STRING"},
            {"name": "atl", "type": "FLOAT"},
            {"name": "atl_date", "type": "STRING"},
            {"name": "snapshot_date", "type": "STRING"},
            {"name": "processing_time", "type": "STRING"}
        ]
    }

    with beam.Pipeline(options=options) as pipeline:
        (
            pipeline
            | 'StartPipeline' >> beam.Create([None])
            | 'FetchMarketData' >> beam.ParDo(FetchCryptoMarketSnapshot())
            | 'WriteToBigQuery' >> beam.io.WriteToBigQuery(
                table=output_table,
                schema=schema,
                write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND,
                create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED,
                custom_gcs_temp_location='gs://blockpulse-data-bucket/temp/'
            )
        )


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)
    run()