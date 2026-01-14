# GitHub Copilot instructions for mini-platform ⚙️

Quick summary

- Purpose: small end-to-end mini platform that shows Postgres -> Debezium (Kafka Connect) -> Kafka -> Spark (Delta) -> MinIO (S3) data flow. Use `docker-compose.yml` as the single entrypoint for local infra.

Architecture & where to look 🔎

- Orchestrator: `docker-compose.yml` — defines `postgres`, `loader`, `zookeeper`, `kafka`, `schema-registry`, `connect`, `minio`, and `spark` services.
- DB loader: `app/load_to_postgres.py` — loads CSVs from `./data` into Postgres (sanitizes table/column names). The `loader` service in compose runs this.
- Connect / Debezium: `connect-docker/Dockerfile` installs `debezium-connector-postgresql` and Avro converter (via `confluent-hub`). Connector is registered via Connect REST (`localhost:8083`).
- Spark jobs: `spark_jobs/` contains examples:
  - `kafka_to_delta.py` (batch read from Kafka -> write Delta to `s3a://lake/customer_delta`)
  - `process.py` (structured streaming example writing Delta to `s3a://lake/processed_data/`)
  - `read_delta.py` (reads Delta from MinIO)

Developer workflows (exact commands) ▶️

1. Start core infra (detached):

   ```bash
   docker-compose up -d postgres zookeeper kafka schema-registry connect minio
   ```

2. Load sample CSVs into Postgres:

   ```bash
   # will read ./data/*.csv and create tables (expects at least 3 CSVs)
   docker-compose run --rm loader
   # or
   docker-compose up loader
   ```

3. Register Debezium Postgres connector (example used in repo):

   ```bash
   curl -i -X POST -H "Accept:application/json" -H "Content-Type:application/json" localhost:8083/connectors/ -d '{
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
   ```

   Note: `docker-compose` sets Avro converters by default for Connect. The example above uses JSON converters (both approaches are used in the repo). If you use Avro, you must have `schema-registry` running and either omit the override or use `AvroConverter` in connector config.

4. Inspect/consume topics (examples used in the repo):

   ```bash
   docker exec -it kafka kafka-topics --bootstrap-server kafka:29092 --list
   docker exec -it kafka kafka-console-consumer --bootstrap-server kafka:29092 --topic dbserver1.public.customer --from-beginning
   ```

5. Run Spark jobs (from the `spark` image):

   - Note: Spark jobs require Delta Lake on the classpath. The code uses `io.delta.sql.DeltaSparkSessionExtension`, so include the delta package at `spark-submit` time.

   ```bash
   # run kafka_to_delta.py (example); include delta package for Spark 3.5.x
   docker-compose run --rm spark spark-submit --packages io.delta:delta-core_2.12:2.4.0 /opt/jobs/kafka_to_delta.py

   # run the streaming example
   docker-compose run --rm spark spark-submit --packages io.delta:delta-core_2.12:2.4.0 /opt/jobs/process.py

   # read the written delta
   docker-compose run --rm spark spark-submit --packages io.delta:delta-core_2.12:2.4.0 /opt/jobs/read_delta.py
   ```

Key project-specific patterns & gotchas ⚠️

- Topic name mismatch to watch for: `spark_jobs/kafka_to_delta.py` uses `pg.public.customer` while `spark_jobs/process.py` subscribes to `dbserver1.public.customer`. The actual topic name depends on your connector `topic.prefix` (see connector example above). Make sure the prefix in the connector matches what your Spark job subscribes to.
- Debezium envelope: code expects Debezium-style payloads (payload.op, payload.after). `kafka_to_delta.py` parses `after` as a `MapType` and writes the raw map; adjust JSON/schema parsing in `kafka_to_delta.py` if you need typed fields.
- MinIO / S3A config: MinIO creds are in `docker-compose.yml` (`MINIO_ROOT_USER=minio`, `MINIO_ROOT_PASSWORD=minio12345`). Spark jobs configure S3A to point at `http://minio:9000` (see `spark_jobs/*` files).
- Loader sanitizes table and column names using `sanitize_table_name()` in `app/load_to_postgres.py` (removes spaces/dots/dashes, lowercases, replaces with `_`).
- Connect image: `connect-docker/Dockerfile` installs Debezium and Avro converter via `confluent-hub`. Modify it to add/remove connectors.
- Many comments are in Turkish — search code when in doubt (e.g. `# her çalıştırmada tabloyu sıfırlar:` in `load_to_postgres.py`).

Ports & endpoints to know 📡

- Postgres: `localhost:5432` (container `pg`)
- Connect REST: `localhost:8083`
- Schema Registry: `localhost:8081`
- Kafka broker (internal): `kafka:29092`; localhost access uses port `9092` (via `PLAINTEXT_HOST`)
- MinIO: `http://localhost:9000` (console at `9001`)

Tests & CI

- There is no test suite or CI config included — add tests in a way that mirrors how services are brought up (e.g., integration tests that run a subset of `docker-compose` services) if needed.

If anything is unclear, tell me which area you'd like expanded (e.g., connector examples with Avro vs JSON, recommended delta versions for Spark, or a runbook for debugging Connect failures). 🙋‍♂️
