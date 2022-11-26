#!/bin/bash
source activate ../../env/bin/activate
DIR="../../datasets/trainticket/workload"
mkdir $DIR

cd ../../systems/Train-Ticket

docker-compose -f docker-compose-workload.yml down
COMPOSE_HTTP_TIMEOUT=200 docker-compose down && \
docker volume prune -f && docker image prune -f


COMPOSE_HTTP_TIMEOUT=200 docker-compose up -d elasticsearch
sleep 1m
bash ingest-pipeline.sh


mvn clean package
COMPOSE_HTTP_TIMEOUT=200 docker-compose up --build -d
sleep 5m

docker-compose -f docker-compose-workload.yml build

docker run --network host -v $PWD/workload:/mnt/locust ts/workload -f /mnt/locust/locustfile_pptam.py --headless -H http://localhost:8080 -u 20 -r 1 -t 30s
sleep 10s

nohup python ../../datasets-generation/profiler.py $DIR/profile.csv &
t1=$( date +%s )
docker-compose -f docker-compose-workload.yml up
t2=$( date +%s )
echo '0;'$t1';'$t2  >> $DIR/experiments.csv
cd -


python `dirname $0`/../create_datasets_workload.py $DIR 'jaeger-span-*'


