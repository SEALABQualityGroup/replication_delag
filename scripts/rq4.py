#!/usr/bin/env python
# coding: utf-8

# In[1]:


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

load_testing_time = [10, 20, 40, 80, 160]


spark = sparksession()
size_dict = {}

for ltt in load_testing_time:
    path = '../datasets/eshopper/rq4_{}/'.format(ltt)
    exps = pd.read_csv(path + 'experiments.csv' , ';',  header=None)
    for num_exp, row in exps.iterrows():
        from_, to = [int(x) for x in row[1:]]
        traces = (spark.read.option('mergeSchema', 'true')
                      .parquet('{}/{}_{}.parquet'.format(path, from_, to)))
        
        size = traces.count()
        size_dict[('E-Shopper', ltt, num_exp)] = size

for ltt in load_testing_time:
    path = '../datasets/trainticket/rq4_{}/'.format(ltt)
    exps = pd.read_csv(path + 'experiments.csv' , ';',  header=None)
    for num_exp, row in exps.iterrows():
        from_, to = [int(x) for x in row[1:]]
        traces = (spark.read.option('mergeSchema', 'true')
                      .parquet('{}/{}_{}.parquet'.format(path, from_, to))).toPandas()
        size = traces.shape[0]
        size_dict[('Train Ticket', ltt, num_exp)] = size
        
spark.stop()


def get_size(row):
    ltt = int(row['load_testing_time'])
    cs = row['Case study']
    exp = row['exp']
    key = (cs, ltt, exp)

    return size_dict[key]


df_tt = pd.DataFrame(data=None, columns=[])
for t in load_testing_time:
    path = '../results/trainticket/rq4_{}.csv'.format(t)
    df_ = pd.read_csv(path)
    df_ = df_.groupby(['exp', 'algo']).mean().reset_index()
    df_['load_testing_time'] = t
    df_tt = df_tt.append(df_)
df_tt['Case study'] = 'Train Ticket'


df_es = pd.DataFrame(data=None, columns=[])
for t in load_testing_time:
    path = '../results/eshopper/rq4_{}.csv'.format(t)
    df_ = pd.read_csv(path)
    df_ = df_.groupby(['exp', 'algo']).mean().reset_index()
    df_['load_testing_time'] = t
    df_es = df_es.append(df_)
df_es['Case study'] = 'E-Shopper'



df = pd.concat([df_es, df_tt])
df['Technique'] = df.algo.map(lambda a: techniques_labels[a])
df['size'] = df.apply(get_size, axis=1)


def avg_size_label(row, df):
    mean = df[(df.load_testing_time == row['load_testing_time']) & (df['Case study'] == row['Case study'])]['size'].mean()
    return round(mean/1000, 1)

df['avg_size'] =  df.apply(lambda row: avg_size_label(row,df) , axis=1)


table = df.groupby(['Case study', 'Technique', 'load_testing_time']).mean()[['size','time']].reset_index()
table['size'] = table['size'].map(lambda x: round(x/1000, 1))

table = pd.pivot_table(table, columns=['Technique'], index=['Case study', 'size'], values='time')

table = table[['K-means', 'HC', 'KrSa', 'CoTr', 'DeCaf', 'DeLag']]

for c in table.columns:
    table[c] = table[c].map(lambda x: round(x, 1))


table.to_csv('../tables/rq4.csv')

from matplotlib.ticker import ScalarFormatter

sns.set(font_scale=2.5, style="whitegrid")

hue_order = [techniques_labels['bnb'], techniques_labels['ga'], techniques_labels['gra']]

include = (df.algo =='gra') | (df.algo =='bnb') | (df.algo =='ga')
meanprops={"marker":"D", "markerfacecolor":"white","markeredgecolor":"black", "markersize":"5", "markeredgewidth":0.75}
palette = {techniques_labels['bnb']: 'gainsboro',
           techniques_labels['ga']: 'silver',
           techniques_labels['gra']: 'gray'}

g = sns.FacetGrid(data=df[include], col="Case study", sharex=False, sharey=False, aspect=2,height=9,  legend_out=False)
g.map_dataframe(sns.pointplot, x="avg_size", y="time", hue="Technique",
                hue_order=hue_order, 
                palette='Greys',
                linewidth=0.5, linestyles='--')


g.set_xlabels('(avg n$^\circ$requests)/1000')
g.axes[0,0].set_title('E-Shopper')
g.axes[0,1].set_title('Train Ticket')

g.axes[0,0].set_ylabel('Execution time (sec)')

g.axes[0,0].set_yscale("log")
g.axes[0,1].set_yscale("log")


g.axes[0,0].set_ylim(3, 9000)
g.axes[0,1].set_ylim(3, 9000)


g.axes[0,0].yaxis.set_major_formatter(ScalarFormatter())
g.axes[0,1].yaxis.set_major_formatter(ScalarFormatter())


g.add_legend()
plt.tight_layout()

plt.savefig('../figures/rq4_trend.pdf')



df160 = df[(df.load_testing_time == 160)]
df160['time_min'] = df160.time.map(lambda t: t/60)



plt.rcParams['figure.figsize'] = (30, 10)
sns.set(font_scale=1.5, style="whitegrid")

hue_order = [techniques_labels['bnb'], techniques_labels['hierarchical'], techniques_labels['gra']]
meanprops={"marker":"D", "markerfacecolor":"white","markeredgecolor":"black", "markersize":"5", "markeredgewidth":0.75}
palette = {techniques_labels['bnb']: 'whitesmoke',
           techniques_labels['ga']: 'gainsboro',
           techniques_labels['gra']: 'darkgray'}


include = (df160.algo =='gra') | (df160.algo =='ga') | (df160.algo =='bnb')

g = sns.catplot(col="Case study", y="time_min", x="Technique", data=df160[include], kind='box', aspect=1.2, sharey=False,
                 palette=palette, showmeans='True', meanprops=meanprops,
                 width=0.2, linewidth=0.9)


g.axes[0,0].set_title('E-Shopper')
g.axes[0,1].set_title('Train Ticket')

g.set_xlabels('')
g.axes[0,0].set_ylabel('Execution time (min)')

g.add_legend()
plt.tight_layout()

plt.savefig('../figures/rq4_box.pdf')

