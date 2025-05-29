import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions, GoogleCloudOptions, StandardOptions
import requests
from datetime import datetime


class FetchCryptoData(beam.DoFn):
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
                    'name': record.get('name'),
                    'symbol': record.get('symbol'),
                    'price': float(record.get('current_price')),
                    'market_cap': float(record.get('market_cap')),
                    'timestamp': datetime.utcnow().isoformat()
                }
        else:
            raise Exception(f"Failed to fetch data: {response.status_code}, {response.text}")


def run():
    pipeline_options = PipelineOptions()
    pipeline_options.view_as(StandardOptions).runner = 'DataflowRunner'

    p = beam.Pipeline(options=pipeline_options)

    (
        p
        | 'Init' >> beam.Create([None])
        | 'FetchCryptoData' >> beam.ParDo(FetchCryptoData())
        | 'WriteToBigQuery' >> beam.io.WriteToBigQuery(
            table='blockpulse-insights-project.crypto_dataset.crypto_prices',
            schema='name:STRING,symbol:STRING,price:FLOAT,market_cap:FLOAT,timestamp:TIMESTAMP',
            write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND,
            create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED,
            custom_gcs_temp_location='gs://blockpulse-data-bucket/temp/',
            method='STREAMING_INSERTS'
        )
    )

    p.run()


if __name__ == '__main__':
    run()
