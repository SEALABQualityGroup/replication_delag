from functools import reduce

class Metrics:
    def __init__(self, traces, thresholds_dict, frontend, from_, to):
        df = traces.toPandas()
        self.posTraces = df[(df[frontend] > from_) & (df[frontend] <= to)]
        self.negTraces = df[(df[frontend] <= from_) | (df[frontend] > to)]
        self.posCount = self.posTraces.count()[frontend]
        self.thresholdDict = thresholds_dict
        self.frontend = frontend
        self.from_ = from_
        self.to = to
        if self.posCount <= 0:
            raise Exception('No positives')

    def _countInInterval(self, traces, expl):
        filtered = reduce(lambda df, bft: df[(df[bft[0]] >= bft[1]) & (df[bft[0]] < bft[2])],
                          expl,
                          traces)
        return filtered.count()[self.frontend]

    def _computeTpAndFp(self, expl):
        return (self._countInInterval(traces, expl)
                for traces in [self.posTraces, self.negTraces])

    def compute(self, expl):
        tp, fp = self._computeTpAndFp(expl)
        rec = tp / self.posCount
        prec = tp / (tp + fp) if (tp + fp) > 0 else 0
        fmeasure = 2 * (prec * rec) / (prec + rec) if prec > 0 or rec > 0 else 0
        support = tp + fp
        return fmeasure, prec, rec, support


class FeatAndMetrics:
    def __init__(self, features, fmeasure, precision, recall, support):
        self.features = features
        self.fmeasure = fmeasure
        self.precision = precision
        self.recall = recall
        self.support = support
