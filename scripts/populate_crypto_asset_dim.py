import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions, SetupOptions
import requests


class FetchCryptoAssetMetadata(beam.DoFn):
    def process(self, element):
        coin_ids = ['bitcoin', 'ethereum', 'tether', 'binancecoin', 'ripple']  # Add more IDs as needed
        for coin_id in coin_ids:
            url = f"https://api.coingecko.com/api/v3/coins/{coin_id}"
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    data = response.json()
                    yield {
                        'asset_id': data['id'],
                        'name': data['name'],
                        'symbol': data['symbol'],
                        'launch_date': data.get('genesis_date'),
                        'category': data.get('categories')[0] if data.get('categories') else None
                    }
                else:
                    raise Exception(f"Failed to fetch metadata for {coin_id}: {response.status_code}")
            except Exception as e:
                print(f"Error fetching metadata for {coin_id}: {e}")


def run():
    options = PipelineOptions()
    options.view_as(SetupOptions).save_main_session = True

    output_path = 'gs://blockpulse-data-bucket/dimensions/crypto_asset_dim.csv'
    csv_fields = ['asset_id', 'name', 'symbol', 'launch_date', 'category']

    with beam.Pipeline(options=options) as pipeline:
        (
            pipeline
            | 'CreateInit' >> beam.Create([None])
            | 'FetchAssetMetadata' >> beam.ParDo(FetchCryptoAssetMetadata())
            | 'ToCSV' >> beam.Map(lambda row: ','.join([str(row.get(col, '')) for col in csv_fields]))
            | 'WriteToGCS' >> beam.io.WriteToText(
                output_path.replace('.csv', ''),
                file_name_suffix='.csv',
                header=','.join(csv_fields),
                shard_name_template=''
            )
        )


if __name__ == '__main__':
    run()
