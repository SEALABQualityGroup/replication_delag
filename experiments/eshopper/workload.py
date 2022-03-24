from glob import glob
import shutil
import os
import uuid
import json
from pyspark.sql import SparkSession

import pandas as pd
from techniques import GeneticRangeAnalysis, MSSelector
from experiments.utils import sparksession

def create_session():
    elasticsearch_spark_jar = os.environ['ES_SPARK']
    return (SparkSession.builder.master("local[*]")
            .appName("My app")
            .config("spark.executor.memory", "40G")
            .config('spark.sql.catalogImplementation', 'hive')
            .config("spark.driver.memory", "30G")
            .config("spark.sql.caseSensitive", "true")
            .config("spark.driver.extraClassPath", elasticsearch_spark_jar)
            .config("spark.driver.extraJavaOptions", "-Dderby.system.home=/tmp/derby{}".format(uuid.uuid1().hex))
            .config("spark.ui.enabled", "false")
            .getOrCreate())


def get_rpcs(traces, frontend):
    return [c for c in traces.columns if c != 'traceId' and c != 'experiment' and c != frontend]


def thresholdsdict(traces, frontend, sla):
    anomalytraces = traces[traces[frontend]>sla]
    min_bin_freq = anomalytraces.count()*0.05

    rpcs = get_rpcs(traces, frontend)
    mss = MSSelector(traces, min_bin_freq=min_bin_freq)
    return mss.select_foreach(rpcs, parallel=True)

def gra(traces, frontend, sla):
    td = thresholdsdict(traces, frontend, sla)
    max_ = traces.select(frontend).rdd.max()[0]
    gra = GeneticRangeAnalysis(traces, frontend, td, sla, max_)
    pareto, _ = gra.explain(ngen=300, mu=30, lambda_=30)
    best = gra.best(pareto)
    print("Pareto size", len(pareto))
    print('Best sol fitnesses', best.fitness.values)
    print('Best sol number of patterns', len(best))
    return best


datapath = "../../datasets/eshopper/workload"
spark = None

try:
    print(os.getcwd())
    print(datapath + '/sla.json')
    spark = create_session()
    with open(datapath + '/sla.json') as f:
        sla_dict = json.load(f)
    res = {}

    exp = pd.read_csv('{}/experiments.csv'.format(datapath), ';', header=None)
    no_exp = 0
    from_ = exp.iloc[no_exp, 1]
    to = exp.iloc[no_exp, 2]
    for path in glob(datapath + '/*__{}_{}.parquet'.format(from_, to)):
        frontend = path.split('/')[-1].split('__')[0]
        traces = (spark.read.option('mergeSchema', 'true')
                .parquet(path))
        print(path)

        if len(get_rpcs(traces, frontend)) >= 6:
            sla = sla_dict[frontend]
            print('Executing ', frontend, '...')
            best = gra(traces,  frontend, sla)
            res[frontend] = best
        
    with open('../../results/eshopper/workload.json', 'w') as f:
        json.dump(res, f)

    spark.stop()
except:
    if spark is not None:
            spark.stop()
