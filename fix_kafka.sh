#!/bin/bash
# Fix Kafka Advertised Listener for External Connectivity

echo "🔧 Fixing Kafka advertised listener..."

# Stop and remove existing Kafka
docker stop chhay-kafka-1 2>/dev/null
docker rm chhay-kafka-1 2>/dev/null

# Get network name
NETWORK=$(docker inspect chhay-zookeeper-1 --format='{{range $k, $v := .NetworkSettings.Networks}}{{$k}}{{end}}')
echo "Using network: $NETWORK"

# Start Kafka with correct advertised listener
docker run -d \
  --name chhay-kafka-1 \
  --network $NETWORK \
  -p 9093:9093 \
  -e KAFKA_BROKER_ID=1 \
  -e KAFKA_ZOOKEEPER_CONNECT=chhay-zookeeper-1:2181 \
  -e KAFKA_LISTENERS=INTERNAL://0.0.0.0:9092,EXTERNAL://0.0.0.0:9093 \
  -e KAFKA_ADVERTISED_LISTENERS=INTERNAL://chhay-kafka-1:9092,EXTERNAL://localhost:9093 \
  -e KAFKA_LISTENER_SECURITY_PROTOCOL_MAP=INTERNAL:PLAINTEXT,EXTERNAL:PLAINTEXT \
  -e KAFKA_INTER_BROKER_LISTENER_NAME=INTERNAL \
  -e KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR=1 \
  -e KAFKA_TRANSACTION_STATE_LOG_MIN_ISR=1 \
  -e KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR=1 \
  confluentinc/cp-kafka:7.5.0

echo "⏳ Waiting for Kafka to start..."
sleep 10

# Check if Kafka is ready
docker exec chhay-kafka-1 kafka-broker-api-versions --bootstrap-server localhost:9093 > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Kafka is ready on port 9093"
    
    # Recreate topics
    echo "📝 Creating topics..."
    docker exec chhay-kafka-1 kafka-topics --bootstrap-server localhost:9093 \
      --create --topic promotion-events --partitions 3 --replication-factor 1 --if-not-exists
    
    docker exec chhay-kafka-1 kafka-topics --bootstrap-server localhost:9093 \
      --create --topic promotion-events-dlq --partitions 1 --replication-factor 1 --if-not-exists
    
    docker exec chhay-kafka-1 kafka-topics --bootstrap-server localhost:9093 \
      --create --topic transactions --partitions 3 --replication-factor 1 --if-not-exists
    
    docker exec chhay-kafka-1 kafka-topics --bootstrap-server localhost:9093 \
      --create --topic AccountCreated.events --partitions 3 --replication-factor 1 --if-not-exists
    
    echo "✅ Topics created"
    
    # List topics
    echo "📋 Available topics:"
    docker exec chhay-kafka-1 kafka-topics --bootstrap-server localhost:9093 --list
else
    echo "❌ Kafka failed to start"
    docker logs chhay-kafka-1 --tail 20
    exit 1
fi

echo ""
echo "🎉 Kafka is now accessible on localhost:9093"
echo "Test with: python3 -c \"from kafka.admin import KafkaAdminClient; print(KafkaAdminClient(bootstrap_servers='localhost:9093').list_topics())\""
