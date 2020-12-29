# DeLag: Detecting Latency Degradation Patterns in Service-based Systems

Replication package of the work "DeLag: Detecting Latency Degradation Patterns in Service-based Systems".

## Requirements
- Python 3.6
- Java 8
- Apache Spark 2.3.1 (set `$SPARK_HOME` env variable with the folder path))
- Elasticsearch for Spark 2.X 7.6.0 (set `$ES_SPARK` env variable with the jar path)
- Maven 3.6.0 (only for datasets generation)
- Docker 18.03 (only for datasets generation)

Use the following command to install Python dependencies
```
pip install --upgrade pip
pip install -r requirements.txt
```

The generation of datasets and the experimentation of techniques were performed on a dual Intel Xeon CPU E5-2650 v3 at 2.30GHz, totaling 40 cores and 80GB of RAM.
Therefore we recommend to run scripts on a machine with similar specs.

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
