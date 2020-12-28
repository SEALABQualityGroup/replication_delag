#!/bin/bash

cd ../../systems/E-Shopper/
NUM_PATTERNS=2

mvn clean install
docker-compose -f docker-compose.dev.yml build

for j in $(seq 0 4)
do
  DIR="../../datasets_/eshopper/rq3_${j}0"
  mkdir -p $DIR

  docker-compose -f docker-compose.tracing.yml up -d
  sleep 1m
  bash ingest-pipeline.sh

  for i in $(seq 1 20)
  do
      docker-compose down
      docker-compose -f docker-compose.tracing.yml stop zipkin
      python generate_injections_noise.py "0.$j"
      cd config
      mvn clean package
      cd ..
      docker-compose -f docker-compose.dev.yml build config
      docker-compose up --scale web=3 --scale gateway=2  -d
      sleep 3m
      locust --host=http://localhost  --no-web -c 20 -r 1 --run-time 30s
      docker-compose -f docker-compose.tracing.yml up -d zipkin
      sleep 5s
      t1=$( date +%s )
      locust --host=http://localhost  --no-web -c 20 -r 1 --run-time 5m
      t2=$( date +%s )
      echo $NUM_PATTERNS';'$t1';'$t2  >> $DIR/experiments.csv
      mkdir $DIR'/info_'$t1'_'$t2
      cp config/src/main/resources/shared/* $DIR'/info_'$t1'_'$t2'/'
  done


python `dirname $0`/../create_dataset.py $DIR 'zipkin*' && \
   COMPOSE_HTTP_TIMEOUT=200 docker-compose -f docker-compose.tracing.yml -f docker-compose.yml down && \
   docker volume prune -f && docker image prune -f

done