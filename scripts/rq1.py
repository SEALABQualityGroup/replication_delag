#!/usr/bin/env python
# coding: utf-8

import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd

sns.set(style="whitegrid")
sns.set_palette(sns.color_palette("Set2"))
plt.rcParams['figure.figsize'] = (20, 10)


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


path = '../results/trainticket/rq1.csv'
df_tt = pd.read_csv(path)
df_tt.algo = df_tt.algo.map(lambda a: techniques_labels[a])
df_tt = df_tt.groupby(['algo', 'exp']).mean().reset_index()
df_tt['case study'] = 'Train Ticket'


path = '../results/eshopper/rq1.csv'
df_es = pd.read_csv(path)
df_es.algo = df_es.algo.map(lambda a: techniques_labels[a])
df_es = df_es.groupby(['algo', 'exp']).mean().reset_index()
df_es['case study'] = 'E-Shopper'


df = pd.concat([df_es, df_tt])
df = pd.melt(df, id_vars=['case study', 'exp', 'algo',], var_name='measure',  value_vars=['precision', 'recall','fmeasure'])

fontsize=40

sns.set(font_scale=2.75, style="whitegrid")
g = sns.FacetGrid(df, col='measure', row='case study', height=10, aspect=1.5)

palette = {algo : 'whitesmoke' for algo in order}
palette[techniques_labels['gra']] = 'darkgray'

g = g.map(sns.boxplot,'algo','value', palette=palette, order=order, showmeans=True, width=0.4,linewidth=2,
          meanprops={"marker":"D", "markerfacecolor":"white","markeredgecolor":"black", "markersize":"14"})
g.set_xlabels('')
g.axes[0,0].set_title('$Q_{prec}$', fontsize=fontsize)
g.axes[0,1].set_title('$Q_{rec}$', fontsize=fontsize)
g.axes[0,2].set_title('$Q_{F1}$', fontsize=fontsize)

g.axes[1,0].set_title('')
g.axes[1,1].set_title('')
g.axes[1,2].set_title('')

g.axes[0,0].set_ylabel('E-Shopper')
g.axes[1,0].set_ylabel('Train Ticket')


plt.savefig('../figures/rq1.pdf')


from scipy.stats import wilcoxon


def cliffsdelta(lst1, lst2):
    n = gt = lt = 0.0
    for x in lst1:
        for y in lst2:
            n += 1
            if x > y:  gt += 1
            if x < y:  lt += 1
    return (gt - lt) / n


rows=[]
for cs, df_ in zip(['E-Shopper', 'Train Ticket'],[df_es, df_tt]):
    for algo in order:
        if algo!=techniques_labels['gra']:
            row =[cs, algo]
            for m in ['precision', 'recall', 'fmeasure']:
                x = df_[df_.algo == techniques_labels['gra']][m]
                y = df_[df_.algo == algo][m]
                p = wilcoxon(x, y, alternative='greater')[1]
                es = abs(cliffsdelta(x, y))
                row.append((p, es))
            rows.append(row)


def format_p_es(p_es):
    p, es = p_es
    if p < 0.001:
        s = "<0.001({:.2f})".format(es)
    else:
        s = "{:.3f}({:.2f})".format(p, es)
    return s


table = pd.DataFrame(data=rows, columns=['Case study', 'Technique', 'Precision', 'Recall', 'F1-score'])
table.Precision = table.Precision.map(format_p_es)
table.Recall = table.Recall.map(format_p_es)
table['F1-score'] = table['F1-score'].map(format_p_es)

table.set_index(['Case study', 'Technique']).to_csv('../tables/rq1.csv')




