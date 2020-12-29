import os
import uuid

from operator import itemgetter, add
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import col
from functools import reduce



class Q:
    def __init__(self, traces, backends, num_pat, explanations):
        self.traces = traces
        self.backends = backends
        self.num_pat = num_pat
        self.explanations = explanations
        self.bm = self.best_matches()

    def filterbyexpl(self, expl):
        return reduce(lambda df, bft: df.filter(col(bft[0]) >= bft[1])
                                        .filter(col(bft[0]) < bft[2]),
                      expl,
                      self.traces)

    def compute_expl_fm(self, selected_traces, pat):
        p = self.traces.filter(col('experiment') == pat).count()
        tp = selected_traces.filter(col('experiment') == pat).count()
        prec = tp / selected_traces.count() if selected_traces.count() else 0
        rec = tp / p if p else 0
        return 2 * prec * rec / (prec + rec) if prec + rec else 0

    def bestexpl_for_pat(self):
        for pat in range(self.num_pat):
            best_expl = None
            for i, expl in enumerate(self.explanations):
                selected_traces = self.filterbyexpl(expl)
                fm = self.compute_expl_fm(selected_traces, pat)
                if best_expl:
                    best_expl = max(best_expl, (i, fm), key=itemgetter(1))
                else:
                    best_expl = (i, fm)
            yield (pat, *best_expl)

    def best_matches(self):
        best_pat = {}
        for pat, i, fm in self.bestexpl_for_pat():
            if i in best_pat:
                best_pat[i] = max(best_pat[i], (pat, fm), key=itemgetter(1))
            else:
                best_pat[i] = (pat, fm)
        return [(best_pat[i][0], self.explanations[i]) for i in best_pat]

    def all_positives(self):
        return reduce(DataFrame.union,
                      [self.traces.filter(col('experiment') == pat)
                       for pat in range(self.num_pat)])

    def true_positives(self):
        return reduce(DataFrame.union,
                      [self.filterbyexpl(expl).filter(col('experiment') == pat)
                       for pat, expl in self.bm])

    def total_selected(self):
        return reduce(add,
                      [self.filterbyexpl(expl).count()
                       for _, expl in self.bm])

    def metrics(self):
        prec = self.true_positives().count() / self.total_selected()
        rec =  self.true_positives().count() / self.all_positives().count()
        fm = 2 * prec * rec / (prec + rec)
        return fm, prec, rec

class QClust:
    def __init__(self, df,  num_pat):
        self.df = df
        self.num_pat = num_pat
        self.labels = set(df['pred'])
        self.bm = self.best_matches()

    def compute_expl_fm(self, selected_traces, pat):
        p = len(self.df[self.df['experiment'] == str(pat)])
        tp = len(selected_traces[selected_traces['experiment'] == str(pat)])
        prec = tp / len(selected_traces) if len(selected_traces) else 0
        rec = tp / p if p else 0
        return 2 * prec * rec / (prec + rec) if prec + rec else 0

    def bestexpl_for_pat(self):
        for pat in range(self.num_pat):
            best_expl = None
            for label in self.labels:
                selected_traces = self.df[self.df['pred']==label]
                fm = self.compute_expl_fm(selected_traces, pat)
                if best_expl:
                    best_expl = max(best_expl, (label, fm), key=itemgetter(1))
                else:
                    best_expl = (label, fm)
            yield (pat, *best_expl)

    def best_matches(self):
        best_pat = {}
        for pat, i, fm in self.bestexpl_for_pat():
            if i in best_pat:
                best_pat[i] = max(best_pat[i], (pat, fm), key=itemgetter(1))
            else:
                best_pat[i] = (pat, fm)
        return [(best_pat[i][0], i) for i in best_pat]

    def uniondf(self, x, y):
        return x.union(y)

    def all_positives(self):
        return reduce(self.uniondf,
                      [self.df[self.df['experiment'] == str(pat)].index
                       for pat in range(self.num_pat)])

    def true_positives(self):
        return reduce(self.uniondf,
                      [self.df[(self.df['experiment'] == str(pat)) & (self.df['pred'] == i)].index
                       for pat, i in self.bm])

    def total_selected(self):
        return reduce(add,
                      [len(self.df[self.df['pred'] == i].index)
                       for _, i in self.bm])

    def metrics(self):
        prec = len(self.true_positives()) / self.total_selected()
        rec = len(self.true_positives()) / len(self.all_positives())
        fm = 2 * prec * rec / (prec + rec)
        return fm, prec, rec

def sparksession():
    es_spark_jar = os.environ['ES_SPARK']
    return (SparkSession.builder
                         .master("local[*]")
                         .appName("My app")
                         .config("spark.executor.memory", "40G")
                         .config('spark.sql.catalogImplementation', 'hive')
                         .config("spark.driver.memory", "30G")
                         .config("spark.driver.extraClassPath", es_spark_jar)
                         .config("spark.driver.extraJavaOptions", "-Dderby.system.home=/tmp/derby{}".format(uuid.uuid1().hex))
                         .getOrCreate())
