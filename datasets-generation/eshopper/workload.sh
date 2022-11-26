#!/bin/bash


DIR="../../datasets/eshopper/workload"
mkdir $DIR


cd ../../systems/E-Shopper

mvn clean install
docker-compose -f docker-compose.dev.yml build

docker-compose -f docker-compose.tracing.yml up -d
sleep 1m
bash ingest-pipeline.sh

docker-compose -f docker-compose.tracing.yml stop zipkin
docker-compose -f docker-compose.dev.yml up --scale web=3 --scale gateway=2  -d
sleep 3m

locust --host=http://localhost  --no-web -c 20 -r 1 --run-time 30s
docker-compose -f docker-compose.tracing.yml up -d zipkin
sleep 5s

nohup python ../../datasets-generation/profiler.py $DIR/profile.csv &
t1=$( date +%s )
$JMETER_HOME/bin/jmeter -n -t workload.jmx
t2=$( date +%s )
echo '0;'$t1';'$t2  >> $DIR/experiments.csv

cd -


python `dirname $0`/../create_datasets_workload.py $DIR 'zipkin*'
