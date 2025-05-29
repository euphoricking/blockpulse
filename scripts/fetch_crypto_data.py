import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions, StandardOptions
from datetime import datetime
import requests


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

        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            for record in data:
                yield {
                    'coin_id': record.get('id'),
                    'symbol': record.get('symbol'),
                    'name': record.get('name'),
                    'price': record.get('current_price'),
                    'market_cap': record.get('market_cap'),
                    'total_volume': record.get('total_volume'),
                    'price_change_percentage_24h': record.get('price_change_percentage_24h'),
                    'market_cap_change_percentage_24h': record.get('market_cap_change_percentage_24h'),
                    'high_24h': record.get('high_24h'),
                    'low_24h': record.get('low_24h'),
                    'circulating_supply': record.get('circulating_supply'),
                    'total_supply': record.get('total_supply'),
                    'max_supply': record.get('max_supply'),
                    'ath': record.get('ath'),
                    'ath_date': record.get('ath_date'),
                    'atl': record.get('atl'),
                    'atl_date': record.get('atl_date'),
                    'snapshot_date': datetime.utcnow().strftime('%Y-%m-%d')
                }
        else:
            raise Exception(f"Failed to fetch data: {response.status_code}, {response.text}")


def run():
    options = PipelineOptions()
    options.view_as(StandardOptions).runner = 'DataflowRunner'

    output_table = 'blockpulse-insights-project.crypto_data.crypto_market_snapshot_fact'

    schema = (
        'coin_id:STRING, symbol:STRING, name:STRING, price:FLOAT, market_cap:FLOAT, '
        'total_volume:FLOAT, price_change_percentage_24h:FLOAT, market_cap_change_percentage_24h:FLOAT, '
        'high_24h:FLOAT, low_24h:FLOAT, circulating_supply:FLOAT, total_supply:FLOAT, max_supply:FLOAT, '
        'ath:FLOAT, ath_date:TIMESTAMP, atl:FLOAT, atl_date:TIMESTAMP, snapshot_date:DATE'
    )

    with beam.Pipeline(options=options) as pipeline:
        (
            pipeline
            | 'Start' >> beam.Create([None])
            | 'FetchMarketData' >> beam.ParDo(FetchCryptoMarketSnapshot())
            | 'WriteToBigQuery' >> beam.io.WriteToBigQuery(
                table=output_table,
                schema=schema,
                write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND,
                create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED,
                custom_gcs_temp_location='gs://blockpulse-data-bucket/temp/',
                method='STREAMING_INSERTS'
            )
        )

if __name__ == '__main__':
    run()
