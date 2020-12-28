from functools import reduce
from statistics import mean

class FitnessUtils:
    def __init__(self, backends, pos_hashtable, neg_hashtable):
        self.backends = backends
        self.pos_hashtable = pos_hashtable
        self.neg_hashtable = neg_hashtable

    def _tplist(self, expllist):
        return [self._satisfy_expl(expl, self.pos_hashtable) for expl in expllist]

    def _fplist(self, expllist):
        return [self._satisfy_expl(expl, self.neg_hashtable) for expl in expllist]

    # number of bit equal one
    @classmethod
    def _cardinality(cls, bitstring):
        return bin(bitstring).count('1')

    @classmethod
    def _satisfy_expl(cls, expl, hashtable):
        bs_list = [cls._satisfy_cond(cond, hashtable) for cond in expl]
        return reduce(lambda x, y: x & y, bs_list)

    @classmethod
    def _satisfy_cond(cls, cond, hashtable):
        col, min_, max_ = cond
        bs_min = hashtable[col, min_]
        bs_max = hashtable[col, max_]
        return bs_min & ~ bs_max


    @classmethod
    def _recall(cls, tplist, num_pos):
        bitstring = reduce(lambda x, y: x | y, tplist)
        num_tp = cls._cardinality(bitstring)
        return num_tp / num_pos

    @classmethod
    def _precision(cls, tplist, fplist):
        bs_tp = reduce(lambda x, y: x | y, tplist)
        bs_fp = reduce(lambda x, y: x | y, fplist)
        num_tp = cls._cardinality(bs_tp)
        support = num_tp + cls._cardinality(bs_fp)
        return num_tp / support if support > 0 else 0

    @classmethod
    def _disjointness(cls, tplist, fplist):
        disj = uniqreq = 0
        totreq = sum(map(cls._cardinality, tplist + fplist))
        if totreq > 0 and len(tplist) == len(fplist):
            for i, _ in enumerate(tplist):
                uniqreq += cls._countuniq(i, tplist) + cls._countuniq(i, fplist)
            disj = uniqreq/totreq
        return disj

    @classmethod
    def _countuniq(cls, i, support_list):
        """
        Counts requests identified by the explanation under analysis but not by other explanations in expllist
        :param i: index of the explanation under analysis
        :param support_list: list of supports (bitstrings) (i.e. identified requests for each explanation)
        :return: number of requests identified by the explanation under analysis but not by other explanations
        """
        uniq = support_list[i]
        for j, supp in enumerate(support_list):
            if j != i:
                uniq &= ~supp
        return cls._cardinality(uniq)

    @classmethod
    def _dissimilarity(cls, tplist, fplist, target_col_pos, target_col_neg):
        dissimilarity = 0
        reverse_bitstring = lambda bs: bin(bs).replace('0b', '')[::-1]
        for tp, fp in zip(tplist, fplist):
            reversed_tp = reverse_bitstring(tp)
            reversed_fp = reverse_bitstring(fp)
            values_tp = [val for bit, val in zip(reversed_tp, target_col_pos[::-1]) if bit == '1']
            values_fp = [val for bit, val in zip(reversed_fp, target_col_neg[::-1]) if bit == '1']
            values = values_tp + values_fp
            if values:
                mean_ = mean(values)
                variability = sum((v - mean_)**2 for v in values)
                dissimilarity += variability
        return dissimilarity


    @classmethod
    def _sizesofclusters(cls, tplist, fplist, target_col_pos, target_col_neg):
        sizes=[]
        reverse_bitstring = lambda bs: bin(bs).replace('0b', '')[::-1]
        for tp, fp in zip(tplist, fplist):
            reversed_tp = reverse_bitstring(tp)
            reversed_fp = reverse_bitstring(fp)
            values_tp = [val for bit, val in zip(reversed_tp, target_col_pos[::-1]) if bit == '1']
            values_fp = [val for bit, val in zip(reversed_fp, target_col_neg[::-1]) if bit == '1']
            values = values_tp + values_fp
            sizes.append(len(values))
        return sizes


    def recall(self, expllist):
        tplist = self._tplist(expllist)
        num_pos = self.pos_hashtable['cardinality']
        return self._recall(tplist, num_pos)

    def precision(self, expllist):
        tplist = self._tplist(expllist)
        fplist = self._fplist(expllist)
        return self._precision(tplist, fplist)

    def disjointness(self, expllist):
        tplist = self._tplist(expllist)
        fplist = self._fplist(expllist)
        return self._disjointness(tplist, fplist)

    def harmonic_mean(self, expllist):
        prec = self.precision(expllist)
        rec = self.recall(expllist)
        disj = self.disjointness(expllist)

        den = prec*rec + prec*disj + rec*disj
        num = 3*prec*rec*disj
        return num/den if den else 0

    def fscore(self, expllist):
        prec = self.precision(expllist)
        rec = self.recall(expllist)
        den = prec + rec
        if den != 0:
            score = (2 * prec * rec)/den
        else:
            score = 0
        return score

    def betafscore(self, expllist, beta):
        prec = self.precision(expllist)
        rec = self.recall(expllist)
        den = (beta**2 * prec) + rec
        if den != 0:
            score = (1 + beta**2)*((prec * rec)/den)
        else:
            score = 0
        return score


    def numclusters(self, expllist):
        return len(expllist)

    def dissimilarity(self, expllist):
        tplist = self._tplist(expllist)
        fplist = self._fplist(expllist)
        return self._dissimilarity(tplist, fplist, self.pos_hashtable['target'], self.neg_hashtable['target'])


    def sizesofclusters(self, expllist):
        tplist = self._tplist(expllist)
        fplist = self._fplist(expllist)
        return self._sizesofclusters(tplist, fplist, self.pos_hashtable['target'], self.neg_hashtable['target'])

    def feasible(self, expllist):
        return reduce(lambda b, expl: b and self.recall([expl]) > 0.05, expllist, True)

    def prec_rec_diss(self, expllist):
        return self.precision(expllist), self.recall(expllist), self.dissimilarity(expllist)

    def evaluate(self, expllist):
        fitness = (0, 0, float('inf'))
        if self.feasible(expllist):
            fitness = self.prec_rec_diss(expllist)
        return fitness