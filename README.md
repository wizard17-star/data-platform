# Mini Data Platform - End-to-End CDC & Delta Lake

A complete data engineering project demonstrating modern data pipeline architecture using **PostgreSQL** → **Debezium** → **Kafka** → **Spark** → **Delta Lake** (MinIO) stack.

## 🎯 Project Overview

This platform implements the **Medallion Architecture** pattern:

- **Bronze Layer**: Raw data ingestion from Kafka
- **Silver Layer**: Data cleaning and transformation  
- **Gold Layer**: Dimensional modeling for analytics

### Tech Stack
- PostgreSQL (source database)
- Debezium (Change Data Capture)
- Apache Kafka (streaming)
- Apache Spark (processing)
- Delta Lake + MinIO (storage)
- Docker (containerization)

---

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- 4GB+ RAM
- Git Bash (Windows users)

### Option 1: Automated Setup (Recommended)
```bash
bash deploy.sh
```

### Option 2: Manual Setup

**1. Start all services**
```bash
docker-compose up -d
```

**2. Load sample data**
```bash
docker exec -it loader python /app/load_to_postgres.py
```

**3. Register Debezium CDC connector**
```bash
curl -X POST -H "Content-Type:application/json" localhost:8083/connectors/ -d '{
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

**4. Start Spark streaming job**
```bash
docker-compose run --rm spark spark-submit \
  --packages io.delta:delta-core_2.12:2.4.0 \
  /opt/jobs/process.py
```

---

## 📊 Verify the Pipeline

### Check Kafka Topics
```bash
docker exec kafka kafka-topics --bootstrap-server kafka:29092 --list
docker exec kafka kafka-console-consumer --bootstrap-server kafka:29092 \
  --topic dbserver1.public.customer --from-beginning
```

### View Delta Lake Data
**MinIO UI**: http://localhost:9001 (minio / minio12345)

Folders:
- `/bronze/all_events` - raw messages
- `/silver/customer`, `/silver/product`, `/silver/salesorder` - cleaned data
- `/gold/dim_customer`, `/gold/dim_product`, `/gold/fact_sales` - analytical tables
## 📁 Project Structure

```
mini-platform/
├── docker-compose.yml          # Services orchestration
├── deploy.sh                   # One-command deployment
├── app/
│   ├── load_to_postgres.py     # Data loader
│   ├── Dockerfile
│   └── requirements.txt
├── spark_jobs/
│   ├── process.py              # Spark streaming job
│   └── Dockerfile
├── connect-docker/             # Debezium connector
├── data/
│   ├── customer.csv
│   ├── product.csv
│   └── salesorder.csv
└── README.md
```

---

## 🔧 Troubleshooting

| Issue | Solution |
|-------|----------|
| Containers won't start | `docker-compose logs <service>` |
| Kafka topics not found | Check connector's `topic.prefix` matches Spark job |
| MinIO bucket missing | `docker exec minio mc mb local/lake` |
| Out of memory | Increase Docker RAM (4GB minimum) |

---

## 📝 How It Works

1. **CSV Data** → PostgreSQL tables
2. **Database Changes** → Debezium detects (INSERT/UPDATE/DELETE)
3. **Kafka Topics** → Changes streamed as JSON messages
4. **Spark Jobs** → Consume & transform (Bronze → Silver → Gold)
5. **Delta Lake** → ACID-compliant data warehouse

---

## 🎓 Learning Outcomes

- Real-time CDC architecture patterns
- Streaming data processing with Spark
- Delta Lake for data warehousing
- Docker orchestration
- Medallion Architecture design

---

## 📚 Key Files

- `docker-compose.yml` - Full stack configuration
- `spark_jobs/process.py` - Spark job with layered processing
- `app/load_to_postgres.py` - Sample data loader
- `deploy.sh` - Automated setup script

---

**Created**: January 2026  
**License**: Open Source