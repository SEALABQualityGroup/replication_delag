from operator import itemgetter

from sklearn.ensemble import RandomForestClassifier

class DeCaf:
    def __init__(self, traces, frontend, rpcs, sla):
        df = traces.toPandas()
        anomalytraces = traces[traces[frontend] > sla]
        min_samples_leaf = int(anomalytraces.count() * 0.05)

        X = df[rpcs]
        y = [1 if y_ > sla else 0 for y_ in df[frontend]]
        self.rpcs = rpcs
        self.regr = RandomForestClassifier(n_estimators=50,  min_samples_leaf=min_samples_leaf, bootstrap=False, max_features=0.6)
        self.regr.fit(X, y)

    def _deduplicate(self, predicates):
        d = {}
        for pred, score in predicates:
            p = pred[-1]
            if p not in d or score > d[p][1]:
                d[p] = (pred, score)
        return list(d.values())

    def explain(self, k=10):
        predicates = []

        for estimator in self.regr.estimators_:
            children_left = estimator.tree_.children_left
            children_right = estimator.tree_.children_right
            feature = estimator.tree_.feature
            threshold = estimator.tree_.threshold
            value = estimator.tree_.value
            stack = [(0, [])]
            while len(stack) > 0:
                nodeid, scopepred = stack.pop()
                child_left, child_right = children_left[nodeid], children_right[nodeid]
                if child_left != child_right:
                    score = value[child_left][0][1]/(value[child_left][0][0] + value[child_left][0][1]) - \
                            value[child_right][0][1]/(value[child_right][0][0] + value[child_right][0][1])
                    if score >= 0:
                        pred_ = (self.rpcs[feature[nodeid]], 0, threshold[nodeid] + 1)
                    else:
                        pred_ = (self.rpcs[feature[nodeid]], threshold[nodeid] + 1, 10 ** 6)
                    pred = scopepred + [pred_]
                    predicates.append((pred, abs(score)))
                    stack.append((child_left, pred))
                    stack.append((child_right, pred))

            predicates = self._deduplicate(predicates)

            return [p for p, score in sorted(predicates, key=itemgetter(1), reverse=True)[:k]]