#!/usr/bin/env python
# coding: utf-8

import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
from experiments.utils import sparksession

sns.set(style="whitegrid")
sns.set_palette(sns.color_palette("Set2"))
plt.rcParams['figure.figsize'] = (20, 15)


techniques_labels = {'gra': 'DeLag',
                   'ga': 'CoTr',
                   'bnb': 'KrSa',
                   'decaf':'DeCaf',
                   'kmeans': 'K-means',
                   'hierarchical':'HC'
}

order=[ techniques_labels['kmeans'],
        techniques_labels['hierarchical'],
        techniques_labels['bnb'],
        techniques_labels['ga'],
        techniques_labels['decaf'],
        techniques_labels['gra'],
]

distances = ["00", "05", '10', '15', '20']


df_tt = pd.DataFrame(data=None, columns=[])
for i in distances:
    path = '../results/trainticket/rq2_{}.csv'.format(i)
    df_ = pd.read_csv(path)
    df_ = df_.groupby(['exp', 'algo']).mean().reset_index()
    df_['distance'] = "$L_\mu \cdot 0.{}$".format(i)
    df_tt = df_tt.append(df_)
df_tt['Case study'] = 'Train Ticket'

df_es = pd.DataFrame(data=None, columns=[])
for i in distances:
    path = '../results/eshopper/rq2_{}.csv'.format(i)
    df_ = pd.read_csv(path)
    df_ = df_.groupby(['exp', 'algo']).mean().reset_index()
    df_['distance'] = "$L_\mu \cdot 0.{}$".format(i)

    df_es = df_es.append(df_)
df_es['Case study'] = 'E-Shopper'


df = pd.concat([df_es, df_tt])
df['Technique'] = df.algo.map(lambda a: techniques_labels[a])


sns.set(font_scale=1.7, style="whitegrid")

include = (df.algo =='gra') | (df.algo =='ga') | (df.algo =='bnb')
meanprops={"marker":"D", "markerfacecolor":"white","markeredgecolor":"black", "markersize":"5", "markeredgewidth":0.75}
palette = {techniques_labels['bnb']: 'whitesmoke',
           techniques_labels['ga']: 'gainsboro',
           techniques_labels['gra']: 'darkgray'}

g = sns.catplot(kind='box', row='Case study', x="distance", y="fmeasure", hue="Technique", data=df[include],
                palette=palette ,aspect=2.3, width=0.4, linewidth=0.9,
                showmeans='True', meanprops=meanprops, legend_out=False)
g._legend.set_title('')
g.set_xlabels('')
g.axes[0,0].set_title('E-Shopper')
g.axes[1,0].set_title('Train Ticket')

g.axes[0,0].set_ylabel('$Q_{F1}$')
g.axes[1,0].set_ylabel('$Q_{F1}$')

        
plt.tight_layout()
plt.savefig('../figures/rq2_box.pdf')



sns.set(font_scale=1.7, style="whitegrid")

hue_order = [techniques_labels['kmeans'], techniques_labels['hierarchical'], techniques_labels['decaf']]
include = (df.algo =='hierarchical') | (df.algo =='kmeans') | (df.algo =='decaf')
meanprops={"marker":"D", "markerfacecolor":"white","markeredgecolor":"black", "markersize":"5", "markeredgewidth":0.75}
palette = {techniques_labels['kmeans']: 'whitesmoke',
           techniques_labels['hierarchical']: 'gainsboro',
           techniques_labels['decaf']: 'darkgray'}

g = sns.catplot(kind='box', row='Case study', x="distance", y="fmeasure", hue="Technique", data=df[include],
                palette=palette ,aspect=2.3, width=0.4, linewidth=0.9, hue_order=hue_order,
                showmeans='True', meanprops=meanprops, legend_out=False)
g._legend.set_title('')
g.set_xlabels('')
g.axes[0,0].set_title('E-Shopper')
g.axes[1,0].set_title('Train Ticket')

g.axes[0,0].set_ylabel('$Q_{F1}$')
g.axes[1,0].set_ylabel('$Q_{F1}$')

        
plt.tight_layout()
plt.savefig('../figures/rq2_box_others.pdf')



spark = sparksession()
dist_dict = {}

frontend = 'HomeControllerHome'

for d in distances:
    path = '../datasets/eshopper/rq2_{}/'.format(d)
    exps = pd.read_csv(path + 'experiments.csv' , ';',  header=None)
    for num_exp, row in exps.iterrows():
        from_, to = [int(x) for x in row[1:]]
        traces = (spark.read.option('mergeSchema', 'true')
                      .parquet('{}/{}_{}.parquet'.format(path, from_, to))).toPandas()
        dist = abs(traces[traces.experiment == '1'][frontend].mean() - traces[traces.experiment == '0'][frontend].mean())
        dist_dict[('E-Shopper', d, num_exp)] = dist

frontend = 'ts-travel-service_queryInfo'
for d in distances:
    path = '../datasets/trainticket/rq2_{}/'.format(d)
    exps = pd.read_csv(path + 'experiments.csv' , ';',  header=None)
    for num_exp, row in exps.iterrows():
        from_, to = [int(x) for x in row[1:]]
        traces = (spark.read.option('mergeSchema', 'true')
                      .parquet('{}/{}_{}.parquet'.format(path, from_, to))).toPandas()
        dist = abs(traces[traces.experiment == '1'][frontend].mean() - traces[traces.experiment == '0'][frontend].mean())
        dist_dict[('Train Ticket', d, num_exp)] = dist
        
spark.stop()


def get_patterns_distance(row):
    d = row['distance'].split('.')[-1].replace('$', '')
    cs = row['Case study']
    exp = row['exp']
    key = (cs, d, exp)
    return dist_dict[key]

df['pat_dist'] = df.apply(get_patterns_distance, axis=1)


df_ = df[(df.algo =='gra') |(df.algo =='ga') |(df.algo =='bnb') ]

sns.set(font_scale=1.8,
        style="whitegrid")

row_order = [techniques_labels['bnb'],techniques_labels['ga'],techniques_labels['gra'] ]
col_order = ['E-Shopper', 'Train Ticket']

g = sns.FacetGrid(df_, row='Technique', col='Case study', height=5, aspect=1.3, sharex=False,
                  row_order=row_order,col_order=col_order )
g = g.map(sns.regplot, 'pat_dist', 'fmeasure', ci=False, logx=True, marker='D', color='gray', 
          scatter_kws = {'facecolors':'none',
                         "alpha":1},
          line_kws={ 'linewidth': 1.5}
         )

g.set_xlabels('')
for i, col in enumerate(col_order):
    g.axes[0,i].set_title(col)

g.axes[1,0].set_title('')
g.axes[1,1].set_title('')
g.axes[2,0].set_title('')
g.axes[2,1].set_title('')

for i, row in enumerate(row_order):
    g.axes[i,0].set_ylabel(row+' ($Q_{F1}$)')

plt.tight_layout()
plt.savefig('../figures/rq2_scatter.pdf')

