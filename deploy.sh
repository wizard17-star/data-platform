#!/bin/bash

echo "--- Step 1: Starting Services ---"
docker-compose up -d --remove-orphans
sleep 45

echo "--- Step 2: Preparing MinIO Bucket ---"
docker exec minio mc alias set local http://localhost:9000 minio minio12345
docker exec minio mc mb local/lake || echo "Bucket already exists"

echo "--- Step 3: Loading Data ---"
# Prevent Git Bash path error (C:/Program Files...):
MSYS_NO_PATHCONV=1 docker exec -it loader python /app/load_to_postgres.py

echo "--- Step 4: Registering Debezium JSON Connector ---"
# If already exists, 409 is normal, the script continues.
curl -i -X POST -H "Accept:application/json" -H "Content-Type:application/json" \
localhost:8083/connectors/ -d '{
  "name": "pg-connector",
  "config": {
    "connector.class": "io.debezium.connector.postgresql.PostgresConnector",
    "database.hostname": "pg",
    "database.port": "5432",
    "database.user": "app",
    "database.password": "app",
    "database.dbname": "appdb",
    "topic.prefix": "dbserver1",
    "plugin.name": "pgoutput",
    "key.converter": "org.apache.kafka.connect.json.JsonConverter",
    "value.converter": "org.apache.kafka.connect.json.JsonConverter",
    "key.converter.schemas.enable": "false",
    "value.converter.schemas.enable": "false"
  }
}'

echo "--- Step 5: Starting Spark Pipeline ---"
docker exec -it spark spark-submit \
  --master local[*] \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,io.delta:delta-spark_2.12:3.0.0,org.apache.hadoop:hadoop-aws:3.3.4,com.amazonaws:aws-java-sdk-bundle:1.12.262 \
  //opt/jobs/process.py