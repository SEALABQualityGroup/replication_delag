from glob import glob
import json

from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

from experiments.utils import sparksession

expname = 'trainticket'



spark = sparksession()

def foreach_reqtype(spark, expname):
    datapath = '../datasets/{}/workload'.format(expname)

    exp = pd.read_csv(datapath + '/experiments.csv', delimiter=';', header=None)
    exp_no = 0
    from_, to = exp.iloc[exp_no, 1], exp.iloc[exp_no, 2]
    with open(datapath + '/sla.json') as f1, open('../results/{}/workload.json'.format(expname)) as f2:
        sla_dict = json.load(f1)
        res_dict = json.load(f2)
    
    frontends = ['ts-travel-service_queryInfo', 'ts-travel-plan-service_getByCheapest', 'ts-preserve-service_preserve']

    for frontend in frontends:#path in glob('../data_/{}/*__{}_{}.parquet'.format(expname, from_, to)):
        #frontend = path.split('/')[-1].split('__')[0]
        path = '{}/{}__{}_{}.parquet'.format(datapath,frontend, from_, to)
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


for df, frontend, sla, _ in foreach_reqtype(spark, expname):
        df = df[df[frontend]< df[frontend].quantile(0.99)]
        
        label = frontend.replace('_', ' $\diamond$ ').replace('ts-', 'train-ticket $\diamond$ ')
        sns.histplot(df, x=frontend,  bins=50, color='whitesmoke')
        plt.axvline(sla, color='k', linestyle='--')
        plt.xlabel('Latency\n(milliseconds)')
        plt.ylabel('No. requests')
        plt.text(x=sla+10,y=plt.ylim()[1]*0.9, s='$L_{SLO}$')
        plt.tight_layout()
        plt.savefig('../figures/{}.pdf'.format(frontend))

        plt.close()

no_pattern = 2

for df, frontend, sla, res in foreach_reqtype(spark, expname):
    df = df[df[frontend]< df[frontend].quantile(0.99)].copy()
    label = frontend.replace('_', ' $\diamond$ ').replace('ts-', 'train-ticket $\diamond$ ')
    width, heigth = plt.gcf().get_size_inches()
    fig, axs = plt.subplots(1,2,figsize=(width*len(res),heigth))
    for ax, pat in zip(axs,res):
        print('-'*100)
        satisfy_ = df.apply(lambda r: satisfy(r, pat), axis='columns')
        meet_sla = df[frontend] <= sla
        df['satisfy'] = satisfy_
        sns.histplot(df, x=frontend,hue='satisfy', bins=50, multiple="stack", ax=ax, legend=False, palette={True:'dimgray', False:'whitesmoke'})
        ax.axvline(sla, color='k', linestyle='--')
        ax.set_xlabel('Latency\n(milliseconds)')
        ax.set_ylabel('No. requests')
        ax.text(x=sla+10,y=ax.get_ylim()[1]*0.9, s='$L_{SLO}$')
        pat_label = ""
        for rpc, e_min, e_max in pat:
            rpc_label = rpc.replace('_', '$\diamond$').replace('ts-', '')
            pat_label += r"$\langle$" + "{}, {}, {}".format(rpc_label, int(e_min), int(e_max)) + r"$\rangle$" + '\n'
        ax.text(x=ax.get_xlim()[1],y=ax.get_ylim()[1]*0.7, s=pat_label, ha="right", va='center')
        ax.set_title('P$_{}$'.format(no_pattern))
        no_pattern += 1
        
    plt.tight_layout()
    plt.savefig('../figures/res_{}.pdf'.format(frontend))
    plt.close()