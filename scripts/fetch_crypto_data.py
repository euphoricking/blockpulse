import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions, SetupOptions
import requests
import json
import datetime
import numpy as np


class FetchCryptoData(beam.DoFn):
    def process(self, element):
        url = "https://api.coingecko.com/api/v3/coins/markets"
        params = {
            'vs_currency': 'usd',
            'ids': 'bitcoin,ethereum,tether,binancecoin,solana',
            'order': 'market_cap_desc',
            'per_page': 5,
            'page': 1,
            'sparkline': True,
            'price_change_percentage': '24h'
        }

        response = requests.get(url, params=params)
        data = response.json()

        snapshot_date = datetime.datetime.utcnow().date().isoformat()

        for coin in data:
            prices = coin.get('sparkline_in_7d', {}).get('price', [])
            volatility = float(np.std(prices)) if prices else None

            yield {
                'id': coin['id'],
                'symbol': coin['symbol'],
                'name': coin['name'],
                'current_price': coin['current_price'],
                'market_cap': coin['market_cap'],
                'total_volume': coin['total_volume'],
                'volatility': volatility,
                'snapshot_date': snapshot_date
            }


def run():
    # Configure Beam pipeline options
    options = PipelineOptions()
    options.view_as(SetupOptions).save_main_session = True

    output_path = 'gs://blockpulse-data-bucket/daily_snapshots/crypto_{}.csv'.format(
        datetime.datetime.utcnow().date().isoformat()
    )

    # Define the CSV column order
    csv_fields = [
        'id', 'symbol', 'name', 'current_price',
        'market_cap', 'total_volume', 'volatility', 'snapshot_date'
    ]

    with beam.Pipeline(options=options) as pipeline:
        (
            pipeline
            | 'Start' >> beam.Create([None])
            | 'FetchCryptoData' >> beam.ParDo(FetchCryptoData())
            | 'ToCSV' >> beam.Map(lambda row: ','.join([str(row.get(col, '')) for col in csv_fields]))
            | 'WriteToGCS' >> beam.io.WriteToText(
                output_path.replace('.csv', ''),  # Beam auto-adds suffix
                file_name_suffix='.csv',
                header=','.join(csv_fields),
                shard_name_template=''  # Ensures one CSV file
            )
        )


if __name__ == '__main__':
    run()