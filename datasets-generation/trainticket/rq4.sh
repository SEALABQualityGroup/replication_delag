#!/bin/bash

cd ../../systems/Train-Ticket/
NUM_PATTERNS=2

for j in 10 20 40 80 160
do
  DIR="../../datasets_/trainticket/rq4_${j}"
  mkdir -p $DIR
  COMPOSE_HTTP_TIMEOUT=200 docker-compose up -d elasticsearch
  sleep 1m
  bash ingest-pipeline.sh

  for i in $(seq 1 20)
  do

      COMPOSE_HTTP_TIMEOUT=200 docker-compose down
      docker-compose up -d elasticsearch
      python3 generateinjections_rq1.py
      mvn clean package
      COMPOSE_HTTP_TIMEOUT=200 docker-compose up --build -d
      sleep 5m
      locust --host=http://localhost:8080  --no-web -c 20 -r 1 --run-time 30s
      sleep 10s
      t1=$( date +%s )
      locust --host=http://localhost:8080  --no-web -c 20 -r 1 --run-time "${j}m"
      t2=$( date +%s )
      echo $NUM_PATTERNS';'$t1';'$t2  >> $DIR/experiments.csv
      mkdir $DIR'/info_'$t1'_'$t2
      cp latency-injector/src/main/resources/delays.json $DIR'/info_'$t1'_'$t2'/'
      cp latency-injector/src/main/resources/noises.json $DIR'/info_'$t1'_'$t2'/'
  done

python `dirname $0`/../create_dataset.py $DIR 'jaeger-span-*' && COMPOSE_HTTP_TIMEOUT=200 docker-compose down && \
   docker volume prune -f && docker image prune -f

done

