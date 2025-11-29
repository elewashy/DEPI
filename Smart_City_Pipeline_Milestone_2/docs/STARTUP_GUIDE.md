# 🚀 System Startup Guide

**Quick and comprehensive startup instructions for the Smart City IoT Pipeline**

> 💡 **Estimated Time**: 5-10 minutes from zero to running pipeline

---

## 📑 Table of Contents

- [Pre-Flight Checklist](#-pre-flight-checklist)
- [Quick Start (5 Minutes)](#-quick-start-5-minutes)
- [Step-by-Step Setup](#-step-by-step-setup)
- [Running the Complete Pipeline](#-running-the-complete-pipeline)
- [System Verification](#-system-verification)
- [Web Dashboards](#-web-dashboards)
- [Troubleshooting](#-troubleshooting)

---

## ✅ Pre-Flight Checklist

### System Requirements

Before starting, verify your system meets these requirements:

| Requirement | Minimum | Recommended | Check Command |
|-------------|---------|-------------|---------------|
| **Docker** | 20.10+ | 24.0+ | `docker --version` |
| **Docker Compose** | 2.0+ | 2.20+ | `docker-compose --version` |
| **RAM** | 8 GB | 16 GB | `free -g` (Linux) or `sysctl hw.memsize` (Mac) |
| **Disk Space** | 20 GB free | 50 GB free | `df -h` |
| **CPU Cores** | 2 cores | 4+ cores | `nproc` (Linux) or `sysctl -n hw.ncpu` (Mac) |

### Port Availability

Ensure these ports are **NOT** in use:

```bash
# Check if ports are available (should return empty)
netstat -tuln | grep -E ':(8080|8081|8082|8888|9092|9870|2181)' # Linux
lsof -i -P | grep -E ':(8080|8081|8082|8888|9092|9870|2181)'   # macOS
```

**Required Ports:**
- `8080` - Spark Master UI
- `8081, 18081` - Spark Workers
- `8082` - Airflow UI
- `8888` - Jupyter Notebook
- `9092` - Kafka Broker
- `9870` - HDFS NameNode UI
- `2181` - ZooKeeper

> ⚠️ **If ports are in use**: Stop the conflicting services or modify ports in `docker-compose.yml`

### Network Check

```bash
# Verify Docker networks
docker network ls

# Test internet connectivity (for pulling images)
ping -c 3 docker.io
```

---

## 🚀 Quick Start (5 Minutes)

**For experienced users - complete automated setup:**

```bash
# Navigate to project directory
cd /path/to/DEPI/Smart_City_Pipeline_Milestone_2

# 1. Start all containers (2-3 minutes)
docker-compose up -d && echo "⏳ Waiting for services..." && sleep 120

# 2. Create Kafka topics
for topic in energy traffic bus_gps waste emergency; do
  docker exec kafka kafka-topics --bootstrap-server kafka:9092 \
    --create --topic $topic --partitions 3 --replication-factor 1 2>/dev/null
done && echo "✅ Kafka topics created"

# 3. Setup HDFS directories
docker exec namenode hdfs dfs -mkdir -p /smartcity/{energy,traffic,bus_gps,waste,emergency,models} && \
docker exec namenode hdfs dfs -chmod -R 777 /smartcity && \
echo "✅ HDFS directories created"

# 4. Connect networks
docker network connect data-pipeline-compose_kafka-net spark-master 2>/dev/null
docker network connect data-pipeline-compose_kafka-net spark-notebook 2>/dev/null
echo "✅ Networks connected"

# 5. Install dependencies
docker exec spark-master pip3 install kafka-python && echo "✅ Dependencies installed"

# 6. Verify setup
echo "\n🎉 Setup Complete! Verification:"
echo "=================================="
docker-compose ps | head -10
echo "\n📨 Kafka Topics:"
docker exec kafka kafka-topics --list --bootstrap-server kafka:9092
echo "\n💾 HDFS Structure:"
docker exec namenode hdfs dfs -ls /smartcity/
echo "\n✅ System ready! Access dashboards at http://localhost:8080, :8888, :8082, :9870"
```

> ⏱️ **Total Time**: ~5 minutes (including wait time)

---

## 📋 Step-by-Step Setup

### Step 1: Start Docker Containers

```bash
cd /path/to/phase-1

# Start all services in detached mode
docker-compose up -d
```

**What's happening:**
- Pulling Docker images (first time only): ~5 minutes
- Starting 25+ containers: ~2-3 minutes
- Initializing services: ~2 minutes

**Progress Indicator:**
```bash
# Monitor startup progress
watch -n 5 'docker-compose ps | grep -E "(healthy|Up)"'
# Press Ctrl+C when you see most services "healthy" or "Up"
```

**Wait for Services:**
```bash
# Wait 2 minutes for all services to initialize
sleep 120

# Verify containers are running
docker-compose ps
```

**Expected Output:**
```
NAME                                     STATUS
kafka                                    Up 2 minutes (healthy)
spark-master                             Up 2 minutes
spark-worker-1                           Up 2 minutes
spark-worker-2                           Up 2 minutes
namenode                                 Up 2 minutes (healthy)
datanode                                 Up 2 minutes (healthy)
...
```

> ✅ **Success Criteria**: All containers show "Up" status, critical ones show "(healthy)"

---

### Step 2: Create Kafka Topics

```bash
# Create 5 topics for SmartCity data streams
for topic in energy traffic bus_gps waste emergency; do
  docker exec kafka kafka-topics --bootstrap-server kafka:9092 \
    --create --topic $topic --partitions 3 --replication-factor 1 2>/dev/null
  echo "✅ Created topic: $topic"
done
```

**Configuration:**
- **Partitions**: 3 (for parallel processing)
- **Replication**: 1 (single broker)
- **Retention**: 24 hours (default)

**Verify Topics Created:**
```bash
docker exec kafka kafka-topics --bootstrap-server kafka:9092 --list
```

**Expected Output:**
```
__consumer_offsets
__transaction_state
bus_gps
emergency
energy
traffic
waste
```

> ✅ **Success Criteria**: See all 5 topics (energy, traffic, bus_gps, waste, emergency)

---

### Step 3: Setup HDFS Directories

```bash
# Create directory structure for data lake
docker exec namenode hdfs dfs -mkdir -p /smartcity/{energy,traffic,bus_gps,waste,emergency,models}

# Set permissions (777 for development, use 755 in production)
docker exec namenode hdfs dfs -chmod -R 777 /smartcity

echo "✅ HDFS directories created"
```

**Verify Directories:**
```bash
docker exec namenode hdfs dfs -ls /smartcity/
```

**Expected Output:**
```
drwxrwxrwx   - root supergroup  /smartcity/bus_gps
drwxrwxrwx   - root supergroup  /smartcity/emergency
drwxrwxrwx   - root supergroup  /smartcity/energy
drwxrwxrwx   - root supergroup  /smartcity/models
drwxrwxrwx   - root supergroup  /smartcity/traffic
drwxrwxrwx   - root supergroup  /smartcity/waste
```

> ✅ **Success Criteria**: See 6 directories (5 data streams + models)

---

### Step 4: Connect Docker Networks

```bash
# Connect Spark containers to Kafka network
docker network connect data-pipeline-compose_kafka-net spark-master 2>/dev/null
docker network connect data-pipeline-compose_kafka-net spark-notebook 2>/dev/null

echo "✅ Networks connected"
```

**Why needed:** Allows Spark containers to communicate with Kafka broker

**Verify Connectivity:**
```bash
# Test Kafka reachability from Spark
docker exec spark-master ping -c 2 kafka

# Test HDFS reachability from Spark
docker exec spark-notebook ping -c 2 namenode
```

**Expected Output:** Successful ping responses

> ✅ **Success Criteria**: Ping commands succeed (2 packets transmitted, 2 received)

---

### Step 5: Install Python Dependencies

```bash
# Install kafka-python library in Spark master
docker exec spark-master pip3 install kafka-python

echo "✅ Dependencies installed"
```

**Verify Installation:**
```bash
docker exec spark-master python3 -c "import kafka; print(f'kafka-python {kafka.__version__} installed')"
```

**Expected Output:** `kafka-python 2.x.x installed`

> ✅ **Success Criteria**: `kafka-python` imports without errors

---

### Step 6: Setup Airflow (First Time Only)

```bash
# Connect Airflow services to required networks
for svc in webserver scheduler worker triggerer; do
  docker network connect data-pipeline-compose_kafka-net data-pipeline-compose-airflow-$svc-1 2>/dev/null
  docker network connect data-pipeline-compose_default data-pipeline-compose-airflow-$svc-1 2>/dev/null
  echo "Connected airflow-$svc"
done

# Restart Airflow scheduler to pick up network changes
docker restart data-pipeline-compose-airflow-scheduler-1

# Wait for scheduler to restart
echo "⏳ Waiting for scheduler restart..."
sleep 30

# Verify Airflow health
curl -s http://localhost:8082/health | grep -q "healthy" && echo "✅ Airflow is healthy"

# Unpause the SmartCity DAG
docker exec -u airflow data-pipeline-compose-airflow-webserver-1 \
  airflow dags unpause smartcity_pipeline

echo "✅ Airflow configured"
```

> ✅ **Success Criteria**: Airflow UI accessible at http://localhost:8082 (admin/admin)

---

## 🔄 Running the Complete Pipeline

### Phase 1: Start Data Generation

```bash
# Start data producer (runs for 120 seconds in background)
docker exec -d spark-master bash -c "timeout 120 python3 /opt/scripts/data_producer.py"

echo "✅ Data producer started (will run for 120 seconds)"
echo "📊 Generating ~7,500 events (125 events/sec × 60 sec)"
```

**Monitor Producer:**
```bash
# Check if producer is running
docker exec spark-master ps aux | grep data_producer

# View producer output (if available)
docker logs spark-master --tail 20 | grep "Messages sent"
```

**Wait Strategy:**
```bash
# Wait 10-15 seconds for initial data to accumulate
sleep 15
echo "✅ Initial data accumulated in Kafka"
```

---

### Phase 2: Start Stream Processing

```bash
# Start Spark streaming job (Kafka → HDFS)
docker exec spark-master bash -c "export PATH=\$PATH:/spark/bin && \
  spark-submit --master local[*] \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.0.1 \
  /opt/scripts/stream_to_hdfs.py 90"
```

**What's happening:**
- Reads from 5 Kafka topics every 10 seconds
- Transforms and enriches data
- Writes Parquet files to HDFS (partitioned by date)
- Runs for 90 seconds

> ⏱️ **Duration**: 90 seconds

**Expected Console Output:**
```
2025-11-29 14:30:25 INFO Starting Kafka → HDFS streaming...
2025-11-29 14:30:35 INFO Batch 1: Processed 125 events
2025-11-29 14:30:45 INFO Batch 2: Processed 125 events
...
2025-11-29 14:32:00 INFO Streaming complete. Total: 900+ events processed
```

---

### Phase 3: Verify Data in HDFS

```bash
# Check HDFS storage
docker exec namenode hdfs dfs -du -h /smartcity/

# List Parquet files
docker exec namenode hdfs dfs -ls -R /smartcity/ | grep parquet | head -10
```

**Expected Output:**
```
116.7 K  350.1 K  /smartcity/bus_gps
134.0 K  402.0 K  /smartcity/emergency
120.7 K  362.2 K  /smartcity/energy
96.0 K   288.1 K  /smartcity/traffic
96.2 K   288.6 K  /smartcity/waste
```

> ✅ **Success Criteria**: Each topic directory has data (> 0 bytes)

---

### Phase 4: Train ML Models

```bash
# Copy ML scripts to Spark notebook container
for f in scripts/ml_*.py; do
  docker cp $f spark-notebook:/home/jovyan/
  echo "Copied $(basename $f)"
done

# Train energy prediction model (most important)
docker exec spark-notebook bash -c "HADOOP_USER_NAME=root spark-submit \
  --master local[*] --conf spark.hadoop.fs.defaultFS=hdfs://namenode:9000 \
  /home/jovyan/ml_energy_prediction.py"
```

> ⏱️ **Duration**: 2-3 minutes per model

**Expected Output:**
```
========================================
 ENERGY CONSUMPTION PREDICTION MODEL
========================================

Loading data from HDFS: hdfs://namenode:9000/smartcity/energy
Data loaded: 445 records

Training Random Forest model...
Features: ['building_idx', 'device_idx', 'hour', 'voltage', 'current']
Target: kwh

Model Performance:
  RMSE: 9.75 kWh
  R²: 0.62

✓ Model saved to hdfs://namenode:9000/smartcity/models/energy
```

**Train All Models (Optional):**
```bash
for model in energy traffic bus waste emergency; do
  echo "\n🤖 Training $model model..."
  docker exec spark-notebook bash -c "HADOOP_USER_NAME=root timeout 120 spark-submit \
    --master local[*] --conf spark.hadoop.fs.defaultFS=hdfs://namenode:9000 \
    /home/jovyan/ml_${model}_prediction.py" 2>&1 | tail -20
done
```

> ⏱️ **Total Duration**: ~10-15 minutes for all 5 models

---

## ✅ System Verification

### Health Check Script

```bash
#!/bin/bash
echo "🔍 Smart City Pipeline Health Check"
echo "===================================="

# 1. Container Status
echo "\n🐳 Container Status:"
running=$(docker-compose ps | grep -c "Up")
total=$(docker-compose ps | wc -l)
echo "   Running: $running/$total containers"

# 2. Kafka Topics
echo "\n📨 Kafka Topics:"
topics=$(docker exec kafka kafka-topics --list --bootstrap-server kafka:9092 | grep -E "energy|traffic|bus|waste|emergency" | wc -l)
echo "   Created: $topics/5 topics"

# 3. Kafka Message Counts
echo "\n📊 Kafka Messages:"
for topic in energy traffic bus_gps waste emergency; do
  count=$(docker exec kafka kafka-run-class kafka.tools.GetOffsetShell \
    --broker-list kafka:9092 --topic $topic 2>/dev/null | awk -F: '{sum+=$3} END{print sum}')
  echo "   $topic: ${count:-0} messages"
done

# 4. HDFS Storage
echo "\n💾 HDFS Storage:"
docker exec namenode hdfs dfs -du -h /smartcity/ 2>/dev/null || echo "   HDFS not ready"

# 5. Airflow Status
echo "\n🔄 Airflow DAG:"
dag_status=$(docker exec -u airflow data-pipeline-compose-airflow-webserver-1 \
  airflow dags state smartcity_pipeline 2>/dev/null | tail -1)
echo "   DAG state: ${dag_status:-Not running}"

echo "\n===================================="
echo "✅ Health check complete!"
```

---

## 🌐 Web Dashboards

After startup, access these dashboards in your browser:

| Dashboard | URL | Purpose |
|-----------|-----|---------|
| **Spark Master** | http://localhost:8080 | Monitor Spark jobs, workers, resource usage |
| **HDFS NameNode** | http://localhost:9870 | Browse HDFS files and system health |
| **Jupyter Notebook** | http://localhost:8888 | Interactive data analysis and exploration |
| **Airflow** | http://localhost:8082 | Monitor DAG runs (login: admin/admin) |

### Quick Dashboard Tour

**1. Spark UI (`:8080`)**
- **Workers**: Should show 2 workers with allocated resources
- **Running Applications**: Shows active streaming jobs
- **Completed Applications**: History of finished jobs

**2. HDFS UI (`:9870`)**
- **Overview**: DataNodes status (should be 3)
- **Utilities → Browse**: Navigate `/smartcity/` to see Parquet files
- **Datanodes**: Health of storage nodes

**3. Jupyter (`:8888`)**
- Open `notebooks/data_exploration.ipynb`
- Run cells to analyze stored data

**4. Airflow (`:8082`)**
- **DAGs**: Click `smartcity_pipeline`
- **Graph**: Visualize task dependencies
- **Runs**: View execution history

---

## 🔧 Troubleshooting

### Issue: Containers Won't Start

**Symptoms:** `docker-compose up -d` fails or containers exit immediately

**Solution:**
```bash
# Check logs for failing container
docker-compose logs <service-name>

# Complete reset
docker-compose down -v
docker system prune -f
docker-compose up -d
```

---

### Issue: Kafka Connection Failed

**Symptoms:** Producer can't connect to Kafka

**Solution:**
```bash
# Verify Kafka is accessible
docker exec spark-master ping -c 2 kafka

# Reconnect network
docker network connect data-pipeline-compose_kafka-net spark-master

# Test connection
docker exec spark-master python3 -c "
from kafka import KafkaProducer
producer = KafkaProducer(bootstrap_servers=['kafka:9092'])
print('✅ Kafka reachable')
"
```

---

### Issue: HDFS Safe Mode Stuck

**Symptoms:** Can't write to HDFS, "Name node is in safe mode"

**Solution:**
```bash
# Check safe mode status
docker exec namenode hdfs dfsadmin -safemode get

# Force leave safe mode
docker exec namenode hdfs dfsadmin -safemode leave

# Verify it left
docker exec namenode hdfs dfs -touchz /smartcity/test.txt
docker exec namenode hdfs dfs -rm /smartcity/test.txt
```

---

### Issue: No Data in HDFS

**Symptoms:** Streaming runs but HDFS directories are empty

**Diagnostic Steps:**
```bash
# 1. Check if producer is generating data
docker exec kafka kafka-console-consumer --bootstrap-server kafka:9092 \
  --topic energy --max-messages 1 --timeout-ms 5000

# 2. Check streaming logs
docker logs spark-master --tail 50 | grep -i "error\|exception"

# 3. Verify HDFS connectivity
docker exec spark-master ping -c 2 namenode
```

**Solution:** Usually network connectivity issue - reconnect networks (see Step 4)

---

### Issue: Out of Memory

**Symptoms:** Containers using too much RAM, system slow

**Solution:**
```bash
# Check memory usage
docker stats --no-stream | grep -E "NAME|GB"

# Reduce Spark workers
docker-compose up -d --scale spark-worker-1=0

# Increase Docker memory limit (Docker Desktop)
# Settings → Resources → Memory → 16 GB
```

---

### Issue: Port Already in Use

**Symptoms:** `Bind for 0.0.0.0:8080 failed: port is already allocated`

**Solution:**
```bash
# Find process using port
lsof -i :8080  # macOS
netstat -tuln | grep 8080  # Linux

# Kill process or change port in docker-compose.yml
# Edit: ports: - "8090:8080"  # Change host port to 8090
```

---

## 🎯 Next Steps

Once your system is running:

1. **Explore Data** - Open Jupyter notebook and run analysis
2. **Monitor Pipeline** - Check Airflow DAG every 30 minutes
3. **Train More Models** - Run all 5 ML models
4. **Read Docs** - Check [COMMANDS.md](COMMANDS.md) for advanced operations
5. **Customize** - Modify data schemas in `scripts/data_producer.py`

---

## 📚 Additional Resources

- [README.md](../README.md) - Project overview
- [COMMANDS.md](COMMANDS.md) - Complete command reference

- [DEMO_OUTPUT.md](DEMO_OUTPUT.md) - Sample outputs and results

---

<div align="center">

**[⬆ Back to Top](#-system-startup-guide)**

---

**Last Updated**: November 29, 2025 | **Version**: 2.0

</div>
