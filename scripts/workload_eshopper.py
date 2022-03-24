from glob import glob
import json
import pandas as pd

import seaborn as sns
import matplotlib.pyplot as plt
from scipy import stats
from experiments.utils import sparksession

expname = 'eshopper'
datapath = '../datasets/{}/workload'.format(expname)


exp = pd.read_csv(datapath + '/experiments.csv', delimiter=';', header=None)
exp_no = 0
from_, to = exp.iloc[exp_no, 1], exp.iloc[exp_no, 2]

spark = sparksession()

def foreach_reqtype(spark):
    with open(datapath + '/sla.json') as f1, open('../results/{}/workload.json'.format(expname)) as f2:
        sla_dict = json.load(f1)
        res_dict = json.load(f2)
        
    for path in glob('{}/*__{}_{}.parquet'.format(datapath, from_, to)):
        frontend = path.split('/')[-1].split('__')[0]
        traces = spark.read.option('mergeSchema', 'true').parquet(path)
        if frontend in sla_dict:
            sla = sla_dict[frontend]
            df = traces.toPandas()
            res = res_dict[frontend]
            yield df, frontend, sla, res


def satisfy(row, pattern):
    res = True
    for rpc, e_min, e_max in pattern:
        cond = e_min <= row[rpc] < e_max
        res &= cond
        
    return res


for df, frontend, sla, _ in foreach_reqtype(spark):
        df = df[df[frontend]< df[frontend].quantile(0.99)]
        
        label = 'e-shopper $\diamond$ web $\diamond$ home'
        sns.histplot(df, x=frontend,  bins=50, color='whitesmoke')
        plt.axvline(sla, color='k', linestyle='--')
        plt.xlabel('Latency\n(milliseconds)')
        plt.ylabel('No. requests')
        plt.text(x=sla+1,y=plt.ylim()[1]*0.9, s='$L_{SLO}$')
        plt.tight_layout()
        plt.savefig('../figures/{}.pdf'.format(frontend))

        plt.close()

for df, frontend, sla, res in foreach_reqtype(spark):
    df = df[df[frontend]< df[frontend].quantile(0.99)].copy()
    label = 'e-shopper $\diamond$ web $\diamond$ home'

    for pat in res:
        satisfy_ = df.apply(lambda r: satisfy(r, pat), axis='columns')
        meet_sla = df[frontend] <= sla
        df['satisfy'] = satisfy_
        sns.histplot(df, x=frontend,hue='satisfy', bins=50, multiple="stack", legend=False, palette={True:'dimgray', False:'whitesmoke'})
        plt.axvline(sla, color='k', linestyle='--')
        plt.xlabel('Latency\n(milliseconds)')
        plt.ylabel('No. requests')
        plt.title('P$_1$')
        plt.text(x=sla+2,y=plt.ylim()[1]*0.9, s='$L_{SLO}$')
        pat_label = ""
        pat[0][0] = "products$\diamond$findproduct"
        pat[1][0] = "gateway$\diamond$get"
        for rpc, e_min, e_max in pat:
            rpc_label = rpc#rpc.replace('_', '$\diamond$').replace('ts-', '')
            pat_label += r"$\langle$" + "{}, {}, {}".format(rpc_label, int(e_min), int(e_max)) + r"$\rangle$" + '\n'
        plt.text(x=plt.xlim()[1],y=plt.ylim()[1]*0.7, s=pat_label, ha="right", va='center', zorder=9999)
        plt.tight_layout()
        
        plt.savefig('../figures/res_{}.pdf'.format(frontend))
        plt.close()