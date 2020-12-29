#!/usr/bin/env python
# coding: utf-8


import pandas as pd
from experiments.utils import sparksession, Q, QClust
from techniques import DeCaf, GeneticRangeAnalysis, MSSelector, RangeAnalysis, GA, BranchAndBound
from sklearn.cluster import KMeans, MeanShift, AgglomerativeClustering
from operator import itemgetter
import time
import random
import numpy as np

from sklearn.cluster import estimate_bandwidth

frontend = 'ts-travel-service_queryInfo'
get_rpcs = lambda traces: [c for c in traces.columns if c != 'traceId' and c != 'experiment' and c != frontend]

spark = sparksession()


def kclustering(traces, sla, Clustering):
    rpcs = get_rpcs(traces)
    anomalytraces = traces[traces[frontend] > sla]
    dflist = []
    for k in range(2, 11):
        df = anomalytraces.select(['experiment', 'traceId'] + rpcs).toPandas()
        clust = Clustering(k)
        df['pred'] = clust.fit_predict(df[rpcs])
        dflist.append(df)
    return dflist


def hierarchical(traces, sla):
    return kclustering(traces, sla, AgglomerativeClustering)


def kmeans(traces, sla):
    return kclustering(traces, sla, KMeans)


def meanshift(traces, sla):
    anomalytraces = traces[traces[frontend] > sla]
    rpcs = get_rpcs(traces)
    df = anomalytraces.select(['experiment', 'traceId'] + rpcs).toPandas()
    clust = MeanShift(5)
    df['pred'] = clust.fit_predict(df[rpcs])
    return df


def split_based(traces, sla, explain):
    anomalytraces = traces[traces[frontend] > sla]
    min_bin_freq = anomalytraces.count() * 0.05
    bandwidth = estimate_bandwidth(traces.toPandas()[[frontend]], quantile=0.1)
    mss = MSSelector(anomalytraces, bandwidth=bandwidth, min_bin_freq=min_bin_freq)
    split_points = mss.select(frontend)

    ra = RangeAnalysis(explain, split_points)
    _, _, solutions = ra.explain()

    return list(map(itemgetter(0), solutions))


def thresholdsdict(traces):
    anomalytraces = traces[traces[frontend] > sla]
    min_bin_freq = anomalytraces.count() * 0.05
    rpcs = get_rpcs(traces)
    mss = MSSelector(traces, min_bin_freq=min_bin_freq)
    return mss.select_foreach(rpcs)


def ga(traces, sla):
    td = thresholdsdict(traces)
    rpcs = get_rpcs(traces)
    explain = GA(traces, rpcs, frontend, td).compute
    return split_based(traces, sla, explain)


def bnb(traces, sla):
    td = thresholdsdict(traces)
    explain = BranchAndBound(traces, frontend, td).compute
    return split_based(traces, sla, explain)


def decaf(traces, sla):
    rpcs = get_rpcs(traces)
    dc = DeCaf(traces, frontend, rpcs, sla)
    return dc.explain(10)


def gra(traces, sla):
    td = thresholdsdict(traces)
    max_ = traces.select(frontend).rdd.max()[0]
    gra = GeneticRangeAnalysis(traces, frontend, td, sla, max_)
    pareto, _ = gra.explain(ngen=300, mu=30, lambda_=30)
    best = gra.best(pareto)
    return best


def qopt(traces, rpcs, num_pat, res):
    q = Q(traces, rpcs, num_pat, res)
    return q.metrics()


def qclust(traces, rpcs, num_pat, df):
    q = QClust(df, num_pat)
    return q.metrics()


def qkclust(traces, rpcs, num_pat, dflist):
    qs = [qclust(traces, rpcs, num_pat, df) for df in dflist]
    return max(qs, key=itemgetter(0))


def experiment(algo, q, traces, num_pat):
    rpcs = get_rpcs(traces)
    sla = traces[traces['experiment'] < num_pat].toPandas().min()[frontend]

    t1 = time.perf_counter()

    res = algo(traces, sla)

    t2 = time.perf_counter()

    fm, prec, rec = q(traces, rpcs, num_pat, res)
    t = t2 - t1
    return fm, prec, rec, t


num_rep = 20
algorithms = [("gra", gra, qopt, num_rep),
              ("ga", ga, qopt, num_rep),
              ("bnb", bnb, qopt, 1),
              ("decaf", decaf, qopt, num_rep),
              ("kmeans", kmeans, qkclust, num_rep),
              ("hierarchical", hierarchical, qkclust, num_rep)
              ]

for i in ['00', '05', '10', '15', '20']:
    datapath = '../../datasets/trainticket/rq2_{}/'.format(i)
    respath = '../../datasets/trainticket/rq2_{}.csv'.format(i)
    res = []
    exps = pd.read_csv(datapath + '/experiments.csv', ';', header=None)
    for row in exps.iterrows():
        num_pat, from_, to = [int(x) for x in row[1]]
        traces = (spark.read.option('mergeSchema', 'true')
                  .parquet(datapath + '/%d_%d.parquet' % (from_, to)))

        print(traces.count())
        sla = traces[traces['experiment'] < num_pat].toPandas().min()[frontend]
        for name, algo, q, num_rep in algorithms:
            random.seed(33)
            np.random.seed(33)
            for j in range(num_rep):
                print('Algorithm ', name)
                print('Experiment nr.', row[0])
                fm, prec, rec, t = experiment(algo, q, traces, num_pat)
                print('Quality: ', fm, prec, rec)
                print('Execution time', t, '\n\n\n')
                res.append([row[0], j, num_pat, name, fm, prec, rec, t])
    df = pd.DataFrame(res, columns=['exp', 'trial', 'num_pat', 'algo', 'fmeasure', 'precision', 'recall', 'time'])
    df.to_csv(respath, index=None, header=True)

spark.stop()
