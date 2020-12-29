# DeLag: Detecting Latency Degradation Patterns in Service-based Systems

Replication package of the work "DeLag: Detecting Latency Degradation Patterns in Service-based Systems".

## Requirements
- Python >= 3.6

Use the following command to install dependencies

```
pip install --upgrade pip
pip install -r requirements.txt
```

## Content
#### Datasets
The `datasets` folder contains the datasets of traces used in the evaluation (in parquet format).

#### Datasets generation
The `datasets-generation` folder contains the bash scripts used to generate the datasets used in the evaluation.

#### Techniques
The `techniques` folder contains the implementation of DeLag, CoTr, KrSa and DeCaf. 

#### Experiments
The `experiments` folder contains the Python scripts to executes DeLag and baselines techniques on the generated datasets to answer our RQs.

#### Results 
The `results` folder contains the results of our experimentation.

#### Scripts
The `scripts` folder contains the Python scripts used to generate the figures and tables of the paper.






