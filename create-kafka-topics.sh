#!/bin/bash

echo "Creating Kafka topics..."

docker exec -it $(docker ps -q -f name=kafka) kafka-topics --create \
  --bootstrap-server localhost:9092 \
  --topic transaction.created \
  --partitions 3 \
  --replication-factor 1 \
  --if-not-exists

docker exec -it $(docker ps -q -f name=kafka) kafka-topics --create \
  --bootstrap-server localhost:9092 \
  --topic ledger.events \
  --partitions 3 \
  --replication-factor 1 \
  --if-not-exists

echo "Kafka topics created successfully"
