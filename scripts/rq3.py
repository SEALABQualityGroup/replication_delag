#!/usr/bin/env python
# coding: utf-8

import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd

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

magnitudes = ["00", "10", '20', '30', '40']

df_tt = pd.DataFrame(data=None, columns=[])
for m in magnitudes:
    path = '../results/trainticket/rq3_{}.csv'.format(m)
    df_ = pd.read_csv(path)
    df_ = df_.groupby(['exp', 'algo']).mean().reset_index()
    df_['magnitude'] = "$L_\mu \cdot 0.{}$".format(m) #[round(i*0.1, 1)] * df_.shape[0]
    df_tt = df_tt.append(df_)
df_tt['Case study'] = 'Train Ticket'


df_es = pd.DataFrame(data=None, columns=[])
for m in magnitudes:
    path = '../results/eshopper/rq3_{}.csv'.format(m)
    df_ = pd.read_csv(path)
    df_ = df_.groupby(['exp', 'algo']).mean().reset_index()
    df_['magnitude'] = "$L_\mu \cdot 0.{}$".format(m)

    df_es = df_es.append(df_)
df_es['Case study'] = 'E-Shopper'


# In[5]:


df = pd.concat([df_es, df_tt])
df['Technique'] = df.algo.map(lambda a: techniques_labels[a])


# In[6]:


sns.set(font_scale=1.7, style="whitegrid")

hue_order = [techniques_labels['kmeans'], techniques_labels['hierarchical'], techniques_labels['gra']]

include = (df.algo =='gra') | (df.algo =='kmeans') | (df.algo =='hierarchical')
meanprops={"marker":"D", "markerfacecolor":"white","markeredgecolor":"black", "markersize":"5", "markeredgewidth":0.75}
palette = {techniques_labels['kmeans']: 'whitesmoke',
           techniques_labels['hierarchical']: 'gainsboro',
           techniques_labels['gra']: 'darkgray'}

g = sns.catplot(kind='box', row='Case study', x="magnitude", y="fmeasure", hue="Technique", data=df[include],
                hue_order=hue_order, 
                palette=palette ,
                aspect=2.3, width=0.4, linewidth=0.9, 
                showmeans='True', meanprops=meanprops, legend_out=False)
g._legend.set_title('')
g.set_xlabels('')
g.axes[0,0].set_title('E-Shopper')
g.axes[1,0].set_title('Train Ticket')

g.axes[0,0].set_ylabel('$Q_{F1}$')
g.axes[1,0].set_ylabel('$Q_{F1}$')

plt.tight_layout()
plt.savefig('../figures/rq3_box.pdf')


sns.set(font_scale=1.7, style="whitegrid")

hue_order = [techniques_labels['bnb'], techniques_labels['ga'], techniques_labels['decaf']]

include = (df.algo =='decaf') | (df.algo =='bnb') | (df.algo =='ga')
meanprops={"marker":"D", "markerfacecolor":"white","markeredgecolor":"black", "markersize":"5", "markeredgewidth":0.75}
palette = {techniques_labels['bnb']: 'whitesmoke',
           techniques_labels['ga']: 'gainsboro',
           techniques_labels['decaf']: 'darkgray'}

g = sns.catplot(kind='box', row='Case study', x="magnitude", y="fmeasure", hue="Technique", data=df[include],
                hue_order=hue_order, 
                palette=palette ,
                aspect=2.3, width=0.4, linewidth=0.9, 
                showmeans='True', meanprops=meanprops, legend_out=False)
g._legend.set_title('')
g.set_xlabels('')
g.axes[0,0].set_title('E-Shopper')
g.axes[1,0].set_title('Train Ticket')

g.axes[0,0].set_ylabel('$Q_{F1}$')
g.axes[1,0].set_ylabel('$Q_{F1}$')

plt.tight_layout()
plt.savefig('../figures/rq3_box_others.pdf')

