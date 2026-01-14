# Mini Data Platform - End-to-End CDC & Delta Lake

A modern data engineering platform that captures real-time database changes and processes them through a **Medallion Architecture** (Bronze → Silver → Gold layers).

---

## 🏗 Architecture

### Data Flow

```
PostgreSQL  →  Debezium  →  Kafka  →  Spark  →  Delta Lake
(Source)       (CDC)       (Queue)   (Process)   (Warehouse)
```

### The 3 Layers

| Layer | Purpose | Content | Location |
|-------|---------|---------|----------|
| **Bronze** | Ingest | Raw messages from Kafka | `/bronze/all_events` |
| **Silver** | Refine | Cleaned, validated data | `/silver/{customer,product,salesorder}` |
| **Gold** | Analyze | Star schema (dimensions + facts) | `/gold/{dim_*,fact_*}` |

### Components & Their Role

| Component | Function |
|-----------|----------|
| **PostgreSQL** | Business data source |
| **Debezium** | Captures INSERT/UPDATE/DELETE changes |
| **Kafka** | Distributes change events |
| **Spark** | Transforms & validates data |
| **Delta Lake** | Stores ACID-compliant analytics data |
| **Docker** | Runs everything in containers |

---

## 🚀 Getting Started

### Prerequisites
- Docker & Docker Compose
- 4GB+ RAM
- Git (any shell)

### Quick Start

**Automated (one command)**:
```bash
bash deploy.sh
```

**Manual**:
```bash
# 1. Start all services
docker-compose up -d

# 2. Load sample data
docker exec -it loader python /app/load_to_postgres.py

# 3. Register CDC connector
curl -X POST localhost:8083/connectors/ \
  -H "Content-Type: application/json" \
  -d '{"name": "pg-connector", "config": {...}}'

# 4. Start Spark job
docker-compose run --rm spark spark-submit /opt/jobs/process.py
```

---

## 📁 Project Structure

```
mini-platform/
├── docker-compose.yml         # All services definition
├── deploy.sh                  # Automated setup script
├── README.md                  # This file
│
├── app/                       # Data loader
│   ├── load_to_postgres.py   # CSV → PostgreSQL
│   ├── Dockerfile
│   └── requirements.txt
│
├── spark_jobs/                # Stream processing
│   ├── process.py             # Bronze → Silver → Gold
│   └── Dockerfile
│
├── connect-docker/            # Debezium connector
│   └── Dockerfile
│
└── data/                      # Sample data
    ├── customer.csv
    ├── product.csv
    └── salesorder.csv
```

---

## 💡 How It Works

### 1. Data Source (PostgreSQL)
- Business data stored in tables
- Sample tables: `customer`, `product`, `salesorder`

### 2. Change Detection (Debezium)
- Monitors PostgreSQL replication logs
- Detects all INSERT, UPDATE, DELETE operations
- Creates Kafka topics: `dbserver1.public.{table}`

### 3. Event Streaming (Kafka)
- High-throughput message queue
- Each database change becomes a message
- Multiple consumers can subscribe

### 4. Stream Processing (Spark)
- Reads messages from Kafka
- Processes in 3 layers:
  - **Bronze**: Save raw messages
  - **Silver**: Parse, validate, type-cast
  - **Gold**: Create analytics tables (star schema)

### 5. Data Storage (Delta Lake + MinIO)
- ACID-compliant format
- Supports versioning and time-travel
- Cost-effective S3-compatible storage

---

## 🎯 Key Features

✨ **Real-time**: Changes flow through system in ~100ms  
✨ **Reliable**: ACID compliance, no data loss  
✨ **Scalable**: Handles thousands of events per second  
✨ **Maintainable**: Clean layered architecture  
✨ **Reproducible**: Docker makes setup consistent  

---

## 📊 Medallion Architecture Explained

### Why 3 Layers?

**Bronze (Raw)**
- Store everything as-is from Kafka
- Keep original data for debugging
- Enable replay capability

**Silver (Clean)**
- Parse JSON into structured format
- Validate data types
- Add processing timestamp
- Remove duplicates

**Gold (Analytics)**
- Create star schema (facts + dimensions)
- Optimize for query performance
- Business-ready data

### Example: Customer Data Journey

```
INSERT → PostgreSQL
  ↓
Debezium captures: {"after": {"customerid": 123, "firstname": "Ahmet"}}
  ↓
Kafka topic: dbserver1.public.customer
  ↓
Spark reads: {...}
  ↓
Bronze: raw JSON stored as-is
  ↓
Silver: parsed, typed, validated
  ↓
Gold: DIM_CUSTOMER table created
```

---

## 🐳 Services Overview

All services run in Docker containers:

| Service | Port | Purpose |
|---------|------|---------|
| PostgreSQL | 5432 | Data source |
| Kafka | 9092 | Message broker |
| Kafka Connect | 8083 | Debezium connector |
| MinIO | 9000/9001 | Object storage (UI) |
| Spark | (local) | Stream processor |

**Start/Stop**:
```bash
docker-compose up -d      # Start
docker-compose down       # Stop
docker-compose ps         # Check status
```

---

## 📝 What You Learn

- Real-time CDC (Change Data Capture) patterns
- Event streaming architecture with Kafka
- Stream processing with Spark
- Data warehouse design (Medallion Architecture)
- Delta Lake fundamentals (ACID, versioning)
- Docker containerization & orchestration

---

## 🔗 Repository & Links

**GitHub**: https://github.com/wizard17-star/data-platform

**Key Files**:
- `spark_jobs/process.py` - Main processing logic
- `docker-compose.yml` - Infrastructure as code
- `app/load_to_postgres.py` - Data loading script

---

## 📖 Further Reading

- [Debezium Documentation](https://debezium.io)
- [Apache Kafka Guide](https://kafka.apache.org)
- [Delta Lake Overview](https://delta.io)
- [Spark Structured Streaming](https://spark.apache.org/structured-streaming)

---

*Built with PostgreSQL, Debezium, Kafka, Spark, and Delta Lake*  
*Architecture: Medallion (Bronze → Silver → Gold)*
- `app/load_to_postgres.py` - Sample data loader
- `deploy.sh` - Automated setup script

---

**Created**: January 2026  
**License**: Open Source