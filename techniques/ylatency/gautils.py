import random
from functools import reduce


class Operators:
    def __init__(self, backends, thresholdsDict):
        self.backends = backends
        self.thresholdsDict = thresholdsDict

    def rdm_interval(self, thresholds):
        indexes = [i for i, _ in enumerate(thresholds)]
        from_, to = sorted(random.sample(indexes, k=2))
        return from_, to

    def rdm_cond(self):
        cond = None
        while cond is None:
            indexes = [i for i, _ in enumerate(self.backends)]
            bi = random.choice(indexes)
            b = self.backends[bi]
            thresholds = self.thresholdsDict[b]
            if len(thresholds) > 2:
                from_, to = self.rdm_interval(thresholds)
                cond = (bi, from_, to)
        return cond

    def cx(self, ind1, ind2):
        ind1 |= ind2
        ind2 |= ind1
        size = len(ind1)
        if size > 0:
            chosen = random.sample(ind2, k=random.randint(1, size))
            ind1 ^= set(chosen)
            ind2 ^= ind1
        return ind1, ind2


    def mut(self, individual):
        mutkind = random.randrange(3)
        if mutkind == 0:
            self.mutremove(individual)
        elif mutkind == 1:
            self.mutadd(individual)

        elif mutkind == 2:
            self.mutmodify(individual)

        return individual,


    def mutadd(self, individual):
        newcond = self.rdm_cond()
        exist = [cond for cond in individual if cond[0] == newcond[0]]
        if not exist:
            individual.add(newcond)


    def mutremove(self, individual):
        if len(individual) > 0:
            rdmcond = random.sample(individual, 1)[0]
            individual.remove(rdmcond)


    def mutmodify(self, individual):
        if len(individual) > 0:
            rdmcond = random.sample(individual, 1)[0]
            interval = list(rdmcond[1:])
            b = self.backends[rdmcond[0]]
            thrslen = len(self.thresholdsDict[b])
            interval[random.randrange(2)] = random.randrange(thrslen)
            if interval[0] != interval[1]:
                individual.remove(rdmcond)
                newcond = (rdmcond[0], *sorted(interval))
                individual.add(newcond)


    def feasible(self, individual):
        for bi, fi, ti in individual:
            b = self.backends[bi]
            thresholds = self.thresholdsDict[b]
            if fi == 0 and ti == len(thresholds) - 1:
                return False

        return True

    def genoToPheno(self, ind):
        pheno = set()
        for bi, fi, ti in ind:
            b = self.backends[bi]
            from_ = self.thresholdsDict[b][fi]
            to = self.thresholdsDict[b][ti]
            pheno.add((b, from_, to))
        return pheno


class FitnessUtils:
    def __init__(self, backends, cache):
        self.backends = backends
        self.cache = cache
        self.p = cache['p']
        self.n = cache['n']

    def countOnesInConjunctedBitStrings(self, ind, getter):
        bit = reduce(lambda bx, by: bx & by,
                     map(getter, ind))
        return bin(bit).count("1")

    def getTPBitString(self, backend_idx, threshold):
        backend = self.backends[backend_idx]
        return self.cache[backend, threshold][0]

    def getFPBitString(self, backend_idx, threshold):
        backend = self.backends[backend_idx]
        return self.cache[backend, threshold][1]

    def computeTP(self, ind):
        tp = None
        if len(ind) == 0:
            tp = self.p
        else:
            getter = lambda bft: self.getTPBitString(bft[0], bft[1]) & ~ self.getTPBitString(bft[0], bft[2])
            tp = self.countOnesInConjunctedBitStrings(ind, getter)
        return tp

    def computeFP(self, ind):
        fp = None
        if len(ind) == 0:
            fp = self.n
        else:
            getter = lambda bft: self.getFPBitString(bft[0], bft[1]) & ~ self.getFPBitString(bft[0], bft[2])
            fp = self.countOnesInConjunctedBitStrings(ind, getter)
        return fp

    def computePrecRec(self, ind):
        tp = self.computeTP(ind)
        fp = self.computeFP(ind)
        prec = tp / (tp + fp) if (tp + fp) > 0 else 0
        rec = tp / self.p
        return prec, rec

    def computeFMeasure(self, ind):
        prec, rec = self.computePrecRec(ind)
        return 2 * (prec * rec) / (prec + rec) if prec > 0 or rec > 0 else 0