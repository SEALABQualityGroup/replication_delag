#!/usr/bin/env python
# coding: utf-8

import json
from glob import glob
import re
from functools import  reduce
from itertools import combinations
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

def compute_overlap_num(df, pat_masks):
    if len(pat_masks) <= 1:
        return 0.0
    masks = [mask1 & mask2 for mask1, mask2 in combinations(pat_masks, 2)]
    mask = reduce(operator.or_, masks)
    return len(df[mask])

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
        f1_cell += '{}:{:.2f} | '.format(pat_name, f1).replace('.00', '')
        prec_cell += '{}:{:.2f} | '.format(pat_name, precision).replace('.00', '')
        rec_cell += '{}:{:.2f} | '.format(pat_name, recall).replace('.00', '')

        no_pattern += 1

        pat_masks.append(pat_mask)

            
    patset_mask = reduce(operator.or_, pat_masks)
    f1, precision, recall = metrics(df, patset_mask, slo_mask)
    num = compute_overlap_num(df, pat_masks) #sum(len(df[mask]) for mask in pat_masks) - len(df[patset_mask])
    den = len(df[patset_mask]) #* len(pat_masks)
    overlap =  str(round(num/den, 3)).replace('.000', '')
    f1_cell = '{:.3f} ({})'.format(f1, f1_cell.rstrip(' | ')).replace('.000', '')
    prec_cell = '{:.3f} ({})'.format(precision, prec_cell.rstrip(' | ')).replace('.000', '')
    rec_cell = '{:.3f} ({})'.format(recall, rec_cell.rstrip(' | ')).replace('.000', '')
    name = '{' + name.rstrip(' ').rstrip(',') + '}'

    row = [req_kind, name, prec_cell, rec_cell, f1_cell, overlap]
    rows.append(row)



with pd.option_context("max_colwidth", 1000):
    df =pd.DataFrame(rows, columns=['Request type', 'Pattern Set',  'Precision', 'Recall', 'F1-score', 'Overlap'])
    print(df['F1-score'])
    df['Request type'] = ["$RC_{}$".format(i) for i in range(1,5)]
    repl = lambda matchobj: matchobj.group(0).replace("P", "P$_") + "$"
    for col in ['Pattern Set',  'Precision', 'Recall', 'F1-score']:
        df[col] = df[col].str.replace(r"P\d+", repl, regex=True)
        df[col] = df[col].str.replace("|", "$\mid$")
    df['Pattern Set'] = df['Pattern Set'].str.replace("{", "\{").str.replace("}", "\}")
    df.to_latex('../tables/workload.tex', index=False, escape=False)


spark.stop()
