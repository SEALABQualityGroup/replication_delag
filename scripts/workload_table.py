#!/usr/bin/env python
# coding: utf-8

import json
from glob import glob
import shutil
from functools import  reduce
import operator
import sys

import pandas as pd

sys.path.append('..')
from experiments.utils import sparksession


def foreach_reqtype(spark):
    frontends = [['HomeControllerHome'], ['ts-travel-service_queryInfo', 'ts-travel-plan-service_getByCheapest', 'ts-preserve-service_preserve']]
    for expname, frontends_ in zip(['eshopper', 'trainticket'], frontends):
        datapath = '../datasets/{}/workload'.format(expname)
        exp = pd.read_csv(datapath + '/experiments.csv'.format(expname), delimiter=';', header=None)
        exp_no = 0
        from_, to = exp.iloc[exp_no, 1], exp.iloc[exp_no, 2]
        with open(datapath + '/sla.json'.format(expname)) as f1, open('../results/{}/workload.json'.format(expname)) as f2:
            sla_dict = json.load(f1)
            res_dict = json.load(f2)

        for frontend in frontends_:
            path = '{}/{}__{}_{}.parquet'.format(datapath, frontend, from_, to)
            traces = spark.read.option('mergeSchema', 'true').parquet(path)
            if frontend in sla_dict:
                sla = sla_dict[frontend]
                df = traces.toPandas()
                res = res_dict[frontend]
                yield df, frontend, sla, res



request_kinds = {'HomeControllerHome':'e-shopper__web__home',
                 'ts-travel-service_queryInfo':'train-ticket___travel-service__queryInfo',
                 'ts-travel-plan-service_getByCheapest':'train-ticket__travel-plan-service__getByCheapest',
                 'ts-preserve-service_preserve': 'train-ticket__preserve-service__preserve'}


spark = sparksession()

def metrics(df, mask, slo_mask):
    precision = len(df[mask & slo_mask])/len(df[mask])
    recall = len(df[mask & slo_mask])/len(df[slo_mask])
    f1 = 2 * (precision * recall) / (precision + recall)
    return f1, precision, recall


rows = []
no_pattern = 1

for df, frontend, sla, res in foreach_reqtype(spark):
    pat_masks = []
    slo_mask = df[frontend] > sla
    req_kind = request_kinds[frontend]
    name = ""
    f1_cell = ""
    prec_cell = ""
    rec_cell = ""
    for pat in res:
        pat_mask = True
        for rpc, e_min, e_max in pat:
            cond_mask = (e_min <= df[rpc]) & (df[rpc] < e_max)
            pat_mask &= cond_mask
            f1, precision, recall = metrics(df, cond_mask, slo_mask)
    
        f1, precision, recall = metrics(df, pat_mask, slo_mask)
        pat_name = 'P{}'.format(no_pattern)
        name += pat_name + ', '
        f1_cell += '{}:{:.3f} | '.format(pat_name, f1)
        prec_cell += '{}:{:.3f} | '.format(pat_name, precision)
        rec_cell += '{}:{:.3f} | '.format(pat_name, recall)

        no_pattern += 1

        pat_masks.append(pat_mask)

            
    patset_mask = reduce(operator.or_, pat_masks)
    f1, precision, recall = metrics(df, patset_mask, slo_mask)
    num = sum(len(df[mask]) for mask in pat_masks) - len(df[patset_mask])
    den = len(df[patset_mask]) * len(pat_masks)
    overlap =  round(num/den, 2)
    f1_cell = '{:.3f} ({})'.format(f1, f1_cell.rstrip(' | '))
    prec_cell = '{:.3f} ({})'.format(precision, prec_cell.rstrip(' | ')).replace('.000', '')
    rec_cell = '{:.3f} ({})'.format(recall, rec_cell.rstrip(' | '))
    name = '{' + name.rstrip(' ').rstrip(',') + '}'

    row = [req_kind, name, prec_cell, rec_cell, f1_cell, overlap]
    rows.append(row)



with pd.option_context("max_colwidth", 1000):
    df =pd.DataFrame(rows, columns=['Request type', 'Pattern Set',  'Precision', 'Recall', 'F1-score', 'Overlap'])
    df.to_csv('../tables/workload.csv', index=False)


spark.stop()
