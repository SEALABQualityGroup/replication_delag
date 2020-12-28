from ylatency.ga import GA
from ks.branchandbound import BranchAndBound


class RangeAnalysis:
    def __init__(self, explainInterval, splitPoints):
        self.splitPoints = splitPoints
        self.explainInterval = explainInterval

    def _computeBestSplits(self, i):
        if i == 0:
            return [], 0, ()
        else:
            bestSelectedSplits, bestSumFMeas, bestExplanations = None, None, None
            for j, v in enumerate(self.splitPoints[:i]):
                selectedSplits, sumFmeas, fmeasures = self._computeBestSplits(j)
                exp = self.explainInterval(self.splitPoints[j], self.splitPoints[i])
                fmeas = exp[1]
                sumFmeas += fmeas
                if bestSumFMeas is None or bestSumFMeas < sumFmeas:
                    bestSelectedSplits = selectedSplits + [self.splitPoints[j]]
                    bestSumFMeas = sumFmeas
                    bestExplanations = *fmeasures, exp

            return bestSelectedSplits, bestSumFMeas, bestExplanations

    def explain(self):
        n = len(self.splitPoints) - 1
        return self._computeBestSplits(n)

