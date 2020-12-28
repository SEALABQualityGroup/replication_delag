import random
from itertools import zip_longest
from operator import itemgetter

import numpy as np

class Operator:
    def __init__(self, thresholds_dict, mutprob=0.4):
        self.columns = list(thresholds_dict.keys())
        self.thresholds_dict = thresholds_dict
        self.expl_maxsize = 1
        self.explset_maxsize = 1
        self.mut_prob = mutprob

    def cond(self, col):
        thresholds = self.thresholds_dict[col]
        min_ = random.choice(thresholds[:-1])
        idx = thresholds.index(min_)
        max_ = random.choice(thresholds[idx+1:])
        return col, min_, max_

    def expl(self):
        size = random.randint(1, self.expl_maxsize)
        cols = random.sample(self.columns, k=size)
        return [self.cond(c) for c in cols]

    def expllist(self):
        size = random.randint(1, self.explset_maxsize)
        return [self.expl() for _ in range(size)]

    def cx(self, ind1, ind2):
        mixed = [expl for pair in zip_longest(ind1,ind2) for expl in pair if expl is not None]
        i = random.randrange(1, len(mixed))
        ind1[:] = mixed[:i]
        ind2[:] = mixed[i:]
        return ind1, ind2

    def mut(self, ind):
        self.mut_expllist(ind)
        for expl in ind:
            if np.random.uniform() < self.mut_prob:
                self.mut_expl(expl)
        return ind,

    def mut_expllist(self, expllist):
        choice = random.randrange(3)
        if choice == 0:
            expllist.insert(random.randrange(len(expllist)), self.expl())
        elif choice == 1 and len(expllist) > 1:
            expllist.remove(random.choice(expllist))
        elif choice == 2:
            self.mut_split_expllist(expllist)

    def mut_split_expllist(self, expllist):
        t = self.thresholds_dict
        if expllist:
            expl = random.choice(expllist)
            col = random.choice(self.columns)
            conds = [c for c in expl if c[0] == col]
            if conds and t[col].index(conds[0][2]) - t[col].index(conds[0][1]) > 1:
                cond = conds[0]
                cond1, cond2 = self.split_cond(cond)
                expl1 = [cond1 if c == cond else c for c in expl]
                expl2 = [cond2 if c == cond else c for c in expl]
                expllist.insert(expllist.index(expl), expl1)
                expllist.insert(expllist.index(expl), expl2)
                expllist.remove(expl)
            elif len(t[col]) > 2:
                cond1 = (col, t[col][0], random.choice(t[col][1:-1]))
                cond2 = (col, random.choice(t[col][1:-1]), t[col][-1])
                expl1 = expl + [cond1]
                expl2 = expl + [cond2]
                expllist.insert(expllist.index(expl), expl1)
                expllist.insert(expllist.index(expl), expl2)
                expllist.remove(expl)

    def split_cond(self, cond):
        t = self.thresholds_dict
        split_index = random.randrange(t[cond[0]].index(cond[1]) + 1, t[cond[0]].index(cond[2]))
        cond1 = (cond[0], cond[1], t[cond[0]][split_index])
        cond2 = (cond[0], t[cond[0]][split_index], cond[2])
        return cond1, cond2

    def mut_expl(self, expl):
        choice = random.randrange(2)
        if choice == 0 and len(expl) > 1:
            expl.remove(random.choice(expl))
        elif choice == 1:
            self.mut_expl_addcond(expl)

    def mut_expl_addcond(self, expl):
        columns = [c for c in self.columns if c not in set(map(itemgetter(0), expl))]
        if columns:
            c = random.choice(columns)
            idx = random.randrange(len(expl))
            expl.insert(idx, self.cond(c))
