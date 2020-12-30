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
We recommend to run the scripts of this replication package on a machine with similar specs.

#### Datasets
The `datasets` folder contains the datasets of traces used in the evaluation (in parquet format).
Each row of each dataset represents a request and contains:
- `traceId`: the ID of the request:
- `[requestLatency]`: the overall latency of the request. It is represented by the column `ts-travel-service_queryInfo` in the Train-Ticket case study and by the column `HomeControllerHome` in the E-Shopper case study.
- `experiment`: if equal to `0` (resp. `1`) the request is affected by the ADC <img src="https://render.githubusercontent.com/render/math?math=A_{1}"> (resp. <img src="https://render.githubusercontent.com/render/math?math=A_{2}">) otherwise is not affected by any ADCs.
- `[RPC]`: the cumulative execution time of `[RPC]` within the request.

#### Datasets generation
The `datasets-generation` folder contains the bash scripts used to generate the datasets used in the evaluation.

#### Techniques
The `techniques` folder contains the implementations of DeLag, CoTr, KrSa and DeCaf. In the following you can find the main Python classes used to implement each technique:
- `DeLag`: class `GeneticRangeAnalysis`
- `CoTr`: classes `RangeAnalysis` and `GA`
- `KrSa`: classes `RangeAnalysis` and `BranchAndBound`
- `DeCaf`: class `DeCaf`.

#### Experiments
The `experiments` folder contains the Python scripts used to execute DeLag and baselines techniques on the generated datasets.

#### Results 
The `results` folder contains the results of our experimentation. Each row of each csv file represents a run of a particural technique on a dataset and contains:
- `exp`: the dataset ID.
- `algo`: the technique experimented. The notation used to indicate each techique is described below:
    - `gra`: [DeLag](https://github.com/SEALABQualityGroup/replication_delag) - DeLag: Detecting Latency Degradation Patterns in Service-based Systems
    - `bnb`: [KrSa](https://doi.org/10.1145/2488388.2488450) - Understanding Latency Variations of Black Box Services (WWW 2013)
    - `ga`: [CoTr](https://doi.org/10.1145/3358960.3379126) - Detecting Latency Degradation Patterns in Service-based Systems (ICPE 2020)
    - `decaf` [DeCaf](http://google.com) - DeCaf: Diagnosing and Triaging Performance Issues in Large-Scale Cloud Services (ICSE 2020)
    - `kmeans`: [K-means](https://scikit-learn.org/stable/modules/generated/sklearn.cluster.KMeans.html)
    - `hierarchical`: [HC](https://scikit-learn.org/stable/modules/generated/sklearn.cluster.AgglomerativeClustering.html#sklearn.cluster.AgglomerativeClustering) - Hierachical clustering
- `trial`: the ID of the run (techniques may be repeated multiple times on a dataset to mitigate result variabilility)
- `precision`: effectiveness measure - Precision (<img src="https://render.githubusercontent.com/render/math?math=Q_{prec}">)
- `recall`: effectiveness measure - Recall (<img src="https://render.githubusercontent.com/render/math?math=Q_{rec}">)
- `fmeasure`: effectiveness measure - F1-score  (<img src="https://render.githubusercontent.com/render/math?math=Q_{F1}">)
- `time`: execution time in seconds

#### Scripts
The `scripts` folder contains the Python scripts used to generate the figures and tables of the paper.

#### Systems
The `systems` folder contains the two case study systems.
