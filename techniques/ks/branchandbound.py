from collections import deque
from ..ks.metrics import Metrics, FeatAndMetrics


class Node:
    def __init__(self, explanation, remainingFeatures, mu, parentNode=None):
        self.exp = explanation
        self.remainingFeatures = remainingFeatures
        self.parentNode = parentNode
        self.mu = mu

    def createChild(self, exp, remainingFeatures, mu):
        return Node(exp, remainingFeatures,
                    mu, self)


class BranchAndBound:
    def __init__(self, traces, frontend, threshold_dict):
        self.traces = traces
        self.frontend = frontend
        self.threshold_dict = threshold_dict
        self.features = self.createFeatures(threshold_dict)
        self.metrics = None
        self.bestExp = None
        self.queue = None

    def initMetrics(self, from_, to):
        self.metrics = Metrics(self.traces,
                               self.threshold_dict,
                               self.frontend,
                               from_,
                               to)

    @staticmethod
    def createFeatures(threshold_dict):
        features = set()
        for b in threshold_dict:
            thresholds = threshold_dict[b]
            f = {(b, t, thresholds[i+1]) for i, t in enumerate(thresholds[:-1])}
            features |= f
        return features


    def updateBestSol(self, exp):
        if self.bestExp is None or self.bestExp.fmeasure < exp.fmeasure:
            self.bestExp = exp
        elif self.bestExp.fmeasure == exp.fmeasure and len(self.bestExp.features) > len(exp.features):
            self.bestExp = exp

    def checkRecallBound(self, exp):
        return exp.recall >= self.bestExp.fmeasure / (2 - self.bestExp.fmeasure)

    @staticmethod
    def checkBoundDecrSupp(support, parentSupport,
                           mu, remainingFeatures):
        decrSupp = parentSupport - support
        return decrSupp >= (parentSupport - mu) / len(remainingFeatures)

    def createFirstNode(self, emptyExp):
        return Node(explanation=emptyExp,
                    remainingFeatures=self.features,
                    mu=self.metrics.posCount / emptyExp.precision)

    def createEmptyExp(self):
        emptySet = frozenset()
        metrics = self.metrics.compute(emptySet)
        return FeatAndMetrics(emptySet, *metrics)

    def createExplanation(self, exp, featureToAdd):
        features = exp.features | {featureToAdd}
        metrics = self.metrics.compute(features)
        return FeatAndMetrics(features, *metrics)

    def bestSol(self):
        #TODO consistent data format with GA
        return self.bestExp.features, self.bestExp.fmeasure, self.bestExp.precision, self.bestExp.recall

    def compute(self, from_, to):
        self.initMetrics(from_, to)
        emptyExp = self.createEmptyExp()
        rootNode = self.createFirstNode(emptyExp)
        self.bestExp = emptyExp
        self.queue = deque([rootNode])
        while self.queue:
            node = self.queue.popleft()
            features = node.remainingFeatures.copy()
            parentSupport = node.exp.support
            for featureToAdd in node.remainingFeatures:
                exp = self.createExplanation(node.exp, featureToAdd)
                if self.checkRecallBound(exp) and self.checkBoundDecrSupp(exp.support, parentSupport,
                                                                          node.mu, features):
                    self.updateBestSol(exp)
                    features.remove(featureToAdd)
                    mu = min(node.mu, self.metrics.posCount / exp.precision)
                    withoutRelated = self.withoutRelated(features, featureToAdd)
                    childNode = node.createChild(exp, withoutRelated, mu)
                    self.queue.append(childNode)
        return self.bestSol()

    def withoutRelated(self, features, featureRemoved):
        return {f for f in features if f[0] != featureRemoved[0]}
