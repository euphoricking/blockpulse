import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions, SetupOptions
from datetime import datetime, timedelta

class GenerateDateDimension(beam.DoFn):
    def process(self, element):
        start_date = datetime.strptime('2020-01-01', '%Y-%m-%d')
        end_date = datetime.strptime('2030-12-31', '%Y-%m-%d')

        delta = end_date - start_date
        for i in range(delta.days + 1):
            current = start_date + timedelta(days=i)
            yield {
                'date': current.strftime('%Y-%m-%d'),
                'year': current.year,
                'quarter': (current.month - 1) // 3 + 1,
                'month': current.month,
                'month_name': current.strftime('%B'),
                'day': current.day,
                'day_of_week': current.strftime('%A'),
                'week_of_year': current.isocalendar()[1]
            }

def run():
    options = PipelineOptions()
    options.view_as(SetupOptions).save_main_session = True

    output_path = 'gs://blockpulse-data-bucket/dimensions/date_dim.csv'
    csv_fields = ['date', 'year', 'quarter', 'month', 'month_name', 'day', 'day_of_week', 'week_of_year']

    with beam.Pipeline(options=options) as pipeline:
        (
            pipeline
            | 'CreateInit' >> beam.Create([None])
            | 'GenerateDates' >> beam.ParDo(GenerateDateDimension())
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
