import copy
from math import ceil
from multiprocessing import get_context
from os import cpu_count

from deap import creator, base, tools, algorithms

from ..ylatency.graoperators import Operator
from ..ylatency.grautils import FitnessUtils
from ..ylatency.thresholds import Hashtable


class ParallelHelper:
    @staticmethod
    def make_global(_evaluate):
        global evaluate
        evaluate = _evaluate
        creator.create("Fitness", base.Fitness, weights=(1.0, 1.0, -1.0))
        creator.create("Individual", list, fitness=creator.Fitness)


    @staticmethod
    def evaluate(ind):
        return evaluate(ind)


class GeneticRangeAnalysis:
    def __init__(self, traces, target_col, thresholds_dict, min_, max_):
        columns = list(thresholds_dict.keys())
        ht = Hashtable(traces, columns, target_col, min_, max_)
        self._ops = Operator(thresholds_dict)
        self._fitness = FitnessUtils(columns, ht.positives(thresholds_dict), ht.negatives(thresholds_dict))
        self.toolbox = base.Toolbox()
        self._initga()

    def _initga(self):
        creator.create("Fitness", base.Fitness, weights=(1.0, 1.0, -1.0))
        creator.create("Individual", list, fitness=creator.Fitness)
        self.toolbox.register("individual", tools.initIterate, creator.Individual, self._ops.expllist)
        self.toolbox.register("population", tools.initRepeat, list, self.toolbox.individual)

        self.toolbox.register("mate", self._ops.cx)
        self.toolbox.register("mutate", self._ops.mut)
        self.toolbox.register("select", tools.selNSGA2)

    def _explain_sequential(self, cp, lambda_, mu, mut, ngen, stats, verbose):
        self.toolbox.register("evaluate", self._fitness.evaluate)
        return self._explain(cp, lambda_, mu, mut, ngen, stats, verbose)

    def _explain_parallel(self, cp, lambda_, mu, mut, ngen, stats, verbose):
        processes_ = min(ceil(lambda_/5), cpu_count())
        with get_context("spawn").Pool(processes_, initializer=ParallelHelper.make_global, initargs=(self._fitness.evaluate, )) as pool:
            self.toolbox.register("evaluate", ParallelHelper.evaluate)
            self.toolbox.register("map", pool.map)
            return self._explain(cp, lambda_, mu, mut, ngen, stats, verbose)

    def _explain(self, cp, lambda_, mu, mut, ngen, stats, verbose):
        self._ops.mut_prob = mut
        if stats:
            stats = tools.Statistics()
            stats.register("pop", copy.deepcopy)
        else:
            stats = None
        hof = tools.ParetoFront(lambda ind1, ind2: ind1.fitness.values == ind1.fitness.values)
        pop = self.toolbox.population(n=ngen)
        res, logbook = algorithms.eaMuPlusLambda(pop, self.toolbox,
                                                 mu=mu,
                                                 lambda_=lambda_,
                                                 cxpb=cp, mutpb=mut, ngen=ngen,
                                                 stats=stats, halloffame=hof, verbose=verbose)
        return hof, logbook

    def _best_betafscore(self, pareto, beta):
        fscores = [self._fitness.betafscore(ind, beta) for ind in pareto]
        max_ = max(fscores)
        bests = [ind for ind, fscore in zip(pareto, fscores) if fscore == max_]
        return bests[0] if len(bests) == 1 else min(bests, key=self._fitness.dissimilarity)

    def best(self, pareto):
        bests = [self._best_betafscore(pareto, i/100) for i in range(10, 101)]
        return min(bests, key=self._fitness.dissimilarity)

    def explain(self, mu=30, lambda_=30, ngen=300, cp=0.6, mut=0.4, stats=False, verbose=False, parallel=True):
        explain_ = self._explain_parallel if parallel else self._explain_sequential
        hof, logbook = explain_(cp, lambda_, mu, mut, ngen, stats, verbose)
        return hof, logbook
