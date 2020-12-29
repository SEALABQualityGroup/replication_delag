from deap import base, creator, tools, algorithms
import copy
from ..ylatency.gautils import Operators, FitnessUtils

from ..ylatency.thresholds import Hashtable


class GAImpl:
    def __init__(self, backends, thresholdsDict, cache):
        self.fitnessUtils = FitnessUtils(backends, cache)
        self.ops = Operators(backends, thresholdsDict)
        self.initGA()

    def initGA(self):
        creator.create("Fitness", base.Fitness, weights=(1.0,))
        creator.create("Individual", set, fitness=creator.Fitness)
        self.toolbox = base.Toolbox()
        self.registerAttributes()
        self.registerIndividual()
        self.registerPop()
        self.registerMateMutateAndSelect()
        self.registerEvaluate()

    def registerAttributes(self):
        self.toolbox.register("attribute", self.ops.rdm_cond)

    def registerIndividual(self):
        SIZE_EXPL = 2
        self.toolbox.register("individual",
                              tools.initRepeat,
                              creator.Individual,
                              self.toolbox.attribute,
                              SIZE_EXPL)

    def registerPop(self):
        self.toolbox.register("population",
                              tools.initRepeat,
                              list,
                              self.toolbox.individual)

    def registerMateMutateAndSelect(self):
        self.toolbox.register("mate", self.ops.cx)
        self.toolbox.register("mutate", self.ops.mut)
        self.toolbox.register("select", tools.selTournament, tournsize=20)

    def registerEvaluate(self):
        evaluate = lambda ind: (self.fitnessUtils.computeFMeasure(ind),)
        self.toolbox.register("evaluate", evaluate)
        self.toolbox.decorate("evaluate", tools.DeltaPenalty(self.ops.feasible, 0.0))

    def compute(self, popSize=30, maxGen=300, mutProb=0.4, stats=False):
        if stats:
            stats = tools.Statistics()
            stats.register("pop", copy.deepcopy)
        else:
            stats = None

        self.toolbox.pop_size = popSize
        self.toolbox.max_gen = maxGen
        self.toolbox.mut_prob = mutProb
        pop = self.toolbox.population(n=self.toolbox.pop_size)
        pop = self.toolbox.select(pop, len(pop))
        res, logbook = algorithms.eaMuPlusLambda(pop, self.toolbox, mu=self.toolbox.pop_size,
                                           lambda_=self.toolbox.pop_size,
                                           cxpb=1 - self.toolbox.mut_prob,
                                           mutpb=self.toolbox.mut_prob,
                                           stats=stats,
                                           ngen=self.toolbox.max_gen,
                                           verbose=None)
        return res, logbook

class GA:

    def __init__(self, traces, backends,
                 frontend, thresholds_dict):
        self.traces = traces
        self.backends = backends
        self.frontend = frontend
        self.thresholds_dict = thresholds_dict
        self.logbook = None
        self.fu = None

    def createCache(self, from_, to):
        cacheMaker = Hashtable(self.traces,
                               self.backends,
                               self.frontend,
                               from_,
                               to)
        return cacheMaker.all_in_one(self.thresholds_dict)

    def compute(self, from_, to, stats=False):
        cache = self.createCache(from_, to)
        ga = GAImpl(self.backends, self.thresholds_dict, cache)
        res, logbook = ga.compute(stats=stats)
        if stats:
            self.logbook = logbook
            self.fu = ga.fitnessUtils
        else:
            self.logbook = None
            self.fu = None

        parsed_res = [(ga.ops.genoToPheno(ind),
                       ga.fitnessUtils.computeFMeasure(ind),
                       *ga.fitnessUtils.computePrecRec(ind))
                      for ind in res]

        pheno, fmeasure, prec, rec = max(parsed_res, key=lambda x: (x[1], -len(x[0])))
        return (pheno,
                fmeasure,
                prec,
                rec)
