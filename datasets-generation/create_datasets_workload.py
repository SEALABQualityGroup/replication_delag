import os
import datetime
import csv
import shutil
import sys
from functools import reduce

from pyspark.sql import SparkSession
from pyspark.sql import functions as f
import pandas as pd


def round_to_millis(traces):
    cols = [c for c in traces.columns if c != 'traceId' and c != 'experiment']
    return reduce(lambda df, c: df.withColumn(c, f.round(f.col(c) / 1000)),
                  cols,
                  traces)

def loadExperimentSpans(from_, to, spark):
    #index = 'jaeger-span-*' #'jaeger-span-' + from_.strftime('%Y-%m-%d')

    fromTimestamp = int(from_.timestamp() * 1000000)
    toTimestamp = int(to.timestamp() * 1000000)
    return (spark.read.format("es")
            .option("es.resource", index)
            .load()
            .select('traceId',
                    'experiment')
            .filter(f.col('timestamp').between(fromTimestamp, toTimestamp))
            .filter(f.isnull('parentId'))
            .filter(f.col('kind') == 'SERVER'))


def loadSpans(from_, to, spark):
    #index = 'jaeger-span-*' # 'jaeger-span-' + from_.strftime('%Y-%m-%d')

    fromTimestamp = int(from_.timestamp() * 1000000)
    toTimestamp = int(to.timestamp() * 1000000)
    return (spark.read.format("es")
            .option("es.resource", index)
            .load()
            .select('traceId',
                    # f.concat_ws('_', *['localEndpoint.serviceName', 'name']).alias('endpoint'),
                    f.col('name').alias('endpoint'),
                    'duration',
                    'id',
                    'kind',
                    'timestamp',
                    'parentId')
            .filter(f.col('timestamp').between(fromTimestamp, toTimestamp)))


def create_session(elasticsearch_spark_jar):
    return (SparkSession.builder.master("local[*]")
            .appName("My app")
            .config("spark.executor.memory", "40G")
            .config('spark.sql.catalogImplementation', 'hive')
            .config("spark.driver.memory", "30G")
            .config("spark.sql.caseSensitive", "true")
            .config("spark.driver.extraClassPath", elasticsearch_spark_jar)
            .getOrCreate())


spark = None
elasticsearch_spark_jar = os.environ['ES_SPARK']
datapath = sys.argv[1]
index = sys.argv[2]


try:
    exp = pd.read_csv('{}/experiments.csv'.format(datapath), ';', header=None)
    spark = create_session(elasticsearch_spark_jar)
    for _, (_, from_ts, to_ts) in exp.iterrows():
        from_ = datetime.datetime.fromtimestamp(from_ts)
        to =  datetime.datetime.fromtimestamp(to_ts) #from_ + datetime.timedelta(minutes=1) 


        spans = loadSpans(from_, to, spark)
        pd_spans = spans.toPandas()
        if len(pd_spans)==0:
            continue

        frontend_mapping = pd_spans[pd_spans['traceId'] == pd_spans['id']][['traceId', 'endpoint']]
        frontends = frontend_mapping.endpoint.unique()
        frontends = [fe for fe in frontends if not fe.startswith("jaeger")]
        print(frontends)

        traces = round_to_millis(spans.filter(spans.kind == 'SERVER')
                                .groupBy('traceId', 'endpoint')
                                .agg(f.sum('duration').alias('duration'))
                                .groupby('traceId')
                                .pivot('endpoint')
                                .agg(f.first('duration')))

        pd_traces = traces.toPandas()
        pd_traces = pd_traces.join(frontend_mapping.set_index('traceId'), on='traceId')

        for frontend in frontends:
            filename = '{}/{}__{}_{}.parquet'.format(datapath, frontend, from_ts, to_ts)
            if os.path.exists(filename):
                print( filename + ' already exists')
                continue
            print("Processing " + filename  + '...')

            df = pd_traces[pd_traces['endpoint'] == frontend].drop('endpoint', axis='columns') \
                .dropna(axis='columns', how='all') \
                .fillna(0)
            sdf = spark.createDataFrame(df)
            sdf = sdf.join(loadExperimentSpans(from_, to, spark), on='traceId')
            sdf.write.parquet(filename)

finally:
    if spark is not None:
        if spark is not None:
            spark.stop()
        if os.path.exists('metastore_db'):
            shutil.rmtree('metastore_db')
