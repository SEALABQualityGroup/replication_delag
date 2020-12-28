import os

from pyspark.sql import SparkSession

import reshape

from datetime import datetime
import csv
import shutil
import sys

spark = None
elasticsearch_spark_jar = os.environ['ES_SPARK']
datapath = sys.argv[1]
index = sys.argv[2]

try:
    spark = (SparkSession.builder
             .master("local[*]")
             .appName("My app")
             .config("spark.executor.memory", "40G")
             .config('spark.sql.catalogImplementation', 'hive')
             .config("spark.driver.memory", "30G")
             .config("spark.sql.caseSensitive", "true")
             .config("spark.driver.extraClassPath", elasticsearch_spark_jar)
             .getOrCreate())

    with open('%s/experiments.csv' % datapath , mode='r') as file:
        reader = csv.reader(file, delimiter=';')
        for row in reader:
            num_patterns, from_ts, to_ts = row
            filename = '%s/%s_%s.parquet' % (datapath, from_ts, to_ts)
            if not os.path.exists(filename):
                from_ = datetime.fromtimestamp(int(from_ts))
                to = datetime.fromtimestamp(int(to_ts))
                traces = reshape.create_sum_traces(from_, to, spark, index)
                traces.write.parquet(filename)
finally:
    if spark is not None:
        spark.stop()
        shutil.rmtree('metastore_db')
