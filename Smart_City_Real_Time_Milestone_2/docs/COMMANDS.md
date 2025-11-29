# 📖 Command Reference Guide

**Complete command reference for Smart City IoT pipeline operations**

> 💡 **Tip**: Use `Ctrl+F` to quickly find commands. All commands are copy-paste ready!

---

## 📑 Table of Contents

### Quick Access
- [🚀 Quick Reference Card](#-quick-reference-card)
- [⚡ One-Line Shortcuts](#-one-line-shortcuts)
- [🔄 Complete Workflows](#-complete-workflows)

### By Component
- [🏗️ System Setup](#️-system-setup)
- [📤 Data Producer](#-data-producer)
- [⚡ Spark Streaming](#-spark-streaming)
- [📨 Kafka Operations](#-kafka-operations)
- [💾 HDFS Operations](#-hdfs-operations)
- [🤖 ML Model Training](#-ml-model-training)
- [📊 Monitoring](#-monitoring)
- [🔄 Airflow Operations](#-airflow-operations)
- [🔧 Troubleshooting](#-troubleshooting)

---

## 🚀 Quick Reference Card

**Most commonly used commands - bookmark this section!**

| Action | Command |
|--------|---------|
| **Start everything** | `docker-compose up -d` |
| **Stop everything** | `docker-compose down` |
| **Full reset** | `docker-compose down -v && docker-compose up -d` |
| **Check status** | `docker-compose ps` |
| **Start producer** | `docker exec -d spark-master python3 /opt/scripts/data_producer.py` |
| **Start streaming** | `docker exec spark-master spark-submit /opt/scripts/stream_to_hdfs.py 60` |
| **List Kafka topics** | `docker exec kafka kafka-topics --list --bootstrap-server kafka:9092` |
| **Check HDFS** | `docker exec namenode hdfs dfs -ls /smartcity/` |
| **Train ML model** | `docker exec spark-notebook spark-submit /home/jovyan/ml_energy_prediction.py` |
| **View logs** | `docker logs <container-name> --tail 50` |

---

## ⚡ One-Line Shortcuts

### Aliases (Add to your `.bashrc` or `.zshrc`)

```bash
# Docker Compose shortcuts
alias dc='docker-compose'
alias dcup='docker-compose up -d'
alias dcdown='docker-compose down'
alias dcps='docker-compose ps'
alias dclogs='docker-compose logs -f'

# Kafka shortcuts
alias kafka-topics='docker exec kafka kafka-topics --bootstrap-server kafka:9092'
alias kafka-consume='docker exec kafka kafka-console-consumer --bootstrap-server kafka:9092'

# HDFS shortcuts
alias hdfs='docker exec namenode hdfs dfs'
alias hdfs-ls='docker exec namenode hdfs dfs -ls -R /smartcity/'
alias hdfs-du='docker exec namenode hdfs dfs -du -h /smartcity/'

# Spark shortcuts
alias spark-master='docker exec spark-master'
alias spark-submit='docker exec spark-master spark-submit'
```

### Quick Scripts

**Complete Setup (One Command)**
```bash
# Complete initialization in one go
docker-compose up -d && sleep 120 && \
for topic in energy traffic bus_gps waste emergency; do \
  docker exec kafka kafka-topics --bootstrap-server kafka:9092 --create --topic $topic --partitions 3 --replication-factor 1 2>/dev/null; \
done && \
docker exec namenode hdfs dfs -mkdir -p /smartcity/{energy,traffic,bus_gps,waste,emergency,models} && \
docker exec namenode hdfs dfs -chmod -R 777 /smartcity && \
docker network connect data-pipeline-compose_kafka-net spark-master && \
docker network connect data-pipeline-compose_kafka-net spark-notebook && \
docker exec spark-master pip3 install kafka-python && \
echo "✅ Setup complete!"
```

**Complete Teardown**
```bash
# Stop and remove everything
docker-compose down -v && \
docker network prune -f && \
echo "✅ Teardown complete!"
```

**Quick Health Check**
```bash
# Check all services in one command
echo "🐳 Containers:" && docker-compose ps && \
echo "\n📨 Kafka Topics:" && docker exec kafka kafka-topics --list --bootstrap-server kafka:9092 && \
echo "\n💾 HDFS Storage:" && docker exec namenode hdfs dfs -du -h /smartcity/
```

---

## 🔄 Complete Workflows

### Workflow 1: First-Time Setup (Fresh Start)

```bash
# Step 1: Start all services (3-4 minutes)
docker-compose up -d
sleep 120

# Step 2: Create Kafka topics
for topic in energy traffic bus_gps waste emergency; do
  docker exec kafka kafka-topics --bootstrap-server kafka:9092 \
    --create --topic $topic --partitions 3 --replication-factor 1
done

# Step 3: Setup HDFS directories
docker exec namenode hdfs dfs -mkdir -p /smartcity/{energy,traffic,bus_gps,waste,emergency,models}
docker exec namenode hdfs dfs -chmod -R 777 /smartcity

# Step 4: Connect networks
docker network connect data-pipeline-compose_kafka-net spark-master
docker network connect data-pipeline-compose_kafka-net spark-notebook

# Step 5: Install dependencies
docker exec spark-master pip3 install kafka-python

# Step 6: Verify setup
docker-compose ps
docker exec kafka kafka-topics --list --bootstrap-server kafka:9092
docker exec namenode hdfs dfs -ls /smartcity/

echo "✅ Setup complete! Ready to run the pipeline."
```

### Workflow 2: Run Complete Pipeline (Data Generation → ML Training)

```bash
# Step 1: Start data producer (runs for 120 seconds)
docker exec -d spark-master bash -c "timeout 120 python3 /opt/scripts/data_producer.py"
echo "⏱️ Producer started. Generating data for 120 seconds..."

# Step 2: Wait for some data, then start streaming
sleep 10
docker exec spark-master bash -c "export PATH=\$PATH:/spark/bin && \
  spark-submit --master local[*] \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.0.1 \
  /opt/scripts/stream_to_hdfs.py 90" &

echo "⏱️ Streaming started. Processing for 90 seconds..."
sleep 100

# Step 3: Verify data in HDFS
echo "\n📊 Data in HDFS:"
docker exec namenode hdfs dfs -du -h /smartcity/

# Step 4: Copy ML scripts
for f in ml_energy_prediction.py ml_traffic_prediction.py ml_bus_prediction.py ml_waste_prediction.py ml_emergency_prediction.py; do
  docker cp scripts/$f spark-notebook:/home/jovyan/
done

# Step 5: Train ML models
for model in energy traffic bus waste emergency; do
  echo "\n🤖 Training $model model..."
  docker exec spark-notebook bash -c "HADOOP_USER_NAME=root spark-submit \
    --master local[*] --conf spark.hadoop.fs.defaultFS=hdfs://namenode:9000 \
    /home/jovyan/ml_${model}_prediction.py" 2>&1 | tail -20
done

echo "\n✅ Pipeline complete! Check results in web UIs."
```

### Workflow 3: Daily Monitoring Routine

```bash
# Morning health check
echo "📊 Daily Health Check - $(date)"
echo "===================="

# 1. Container status
echo "\n🐳 Container Status:"
docker-compose ps --format "table {{.Name}}\t{{.Status}}"

# 2. Resource usage
echo "\n💻 Resource Usage:"
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"

# 3. Kafka message counts
echo "\n📨 Kafka Message Counts:"
for topic in energy traffic bus_gps waste emergency; do
  count=$(docker exec kafka kafka-run-class kafka.tools.GetOffsetShell \
    --broker-list kafka:9092 --topic $topic 2>/dev/null | awk -F: '{sum+=$3} END{print sum}')
  echo "  $topic: $count messages"
done

# 4. HDFS storage
echo "\n💾 HDFS Storage:"
docker exec namenode hdfs dfs -du -h /smartcity/

# 5. Airflow DAG status
echo "\n🔄 Airflow DAG Status:"
docker exec -u airflow data-pipeline-compose-airflow-webserver-1 \
  airflow dags list-runs -d smartcity_pipeline | head -5

echo "\n✅ Health check complete!"
```

---

## 🏗️ System Setup

### Start All Services

```bash
# Start containers in detached mode
docker-compose up -d

# Expected duration: 2-3 minutes
# Verify startup
docker-compose ps
```

> ⚠️ **Note**: Wait for all services to be healthy before proceeding

### Create Kafka Topics

```bash
# Create all 5 topics with 3 partitions each
for topic in energy traffic bus_gps waste emergency; do
  docker exec kafka kafka-topics --bootstrap-server kafka:9092 \
    --create --topic $topic --partitions 3 --replication-factor 1 2>/dev/null
done

# Verify topics were created
docker exec kafka kafka-topics --bootstrap-server kafka:9092 --list
```

**Expected output:**
```
__consumer_offsets
__transaction_state
bus_gps
emergency
energy
traffic
waste
```

### Create HDFS Directories

```bash
# Create directory structure for all data streams
docker exec namenode hdfs dfs -mkdir -p /smartcity/{energy,traffic,bus_gps,waste,emergency,models}

# Set permissions (777 for development, restrict in production)
docker exec namenode hdfs dfs -chmod -R 777 /smartcity

# Verify directories
docker exec namenode hdfs dfs -ls /smartcity/
```

### Connect Networks

```bash
# Connect Spark to Kafka network
docker network connect data-pipeline-compose_kafka-net spark-master
docker network connect data-pipeline-compose_kafka-net spark-notebook

# Connect Spark to HDFS network (default network)
docker network connect data-pipeline-compose_default spark-notebook

# Verify connectivity
docker exec spark-master ping -c 2 kafka
docker exec spark-notebook ping -c 2 namenode
```

### Check Container Status

```bash
# Simple status
docker-compose ps

# Detailed status with ports
docker-compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"

# Check specific container
docker inspect <container-name> | grep -i status
```

---

## 📤 Data Producer

### Start SmartCity Data Producer

```bash
# Standard run (120 seconds)
docker exec spark-master timeout 120 python3 /opt/scripts/data_producer.py

# Expected output: Generates 25 events/batch × 5 topics every 2 seconds
```

### Run in Background

```bash
# Run for 5 minutes in background
docker exec -d spark-master bash -c "timeout 300 python3 /opt/scripts/data_producer.py"

# Run indefinitely (until manually stopped)
docker exec -d spark-master python3 /opt/scripts/data_producer.py
```

### Check Producer Status

```bash
# Check if producer is running
docker exec spark-master ps aux | grep data_producer

# View live output (if running in foreground)
docker logs spark-master -f | grep "Messages sent"
```

### View Producer Output

```bash
# View last 20 lines of producer output
docker exec spark-master tail -20 /tmp/producer.log

# Follow producer logs in real-time
docker exec spark-master tail -f /tmp/producer.log
```

### Stop Producer

```bash
# Kill producer process
docker exec spark-master pkill -f data_producer.py

# Verify it stopped
docker exec spark-master ps aux | grep data_producer
```

---

## ⚡ Spark Streaming

### Start Streaming (Kafka → HDFS)

```bash
# Standard streaming job (60 seconds)
docker exec spark-master bash -c "export PATH=\$PATH:/spark/bin && \
  spark-submit --master local[*] \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.0.1 \
  /opt/scripts/stream_to_hdfs.py 60"
```

> ⏱️ **Duration**: Runs for specified seconds (60 in example above)

### Run in Background

```bash
# Run for 2 minutes in background with logging
docker exec -d spark-master bash -c "export PATH=\$PATH:/spark/bin && \
  timeout 120 spark-submit --master local[*] \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.0.1 \
  /opt/scripts/stream_to_hdfs.py 90 2>&1 | tee /tmp/streaming.log"
```

### Demo Streaming (Real-time View)

```bash
# Show real-time data processing (with console output)
docker exec spark-master bash -c "export PATH=\$PATH:/spark/bin && \
  spark-submit --master local[*] \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.0.1 \
  /opt/scripts/demo_streaming.py"
```

> 💡 **Tip**: This shows live stats - great for demos!

### View Streaming Logs

```bash
# View last 50 lines of streaming logs
docker exec spark-master tail -50 /tmp/streaming.log

# Follow logs in real-time
docker exec spark-master tail -f /tmp/streaming.log

# Search for errors
docker exec spark-master grep -i error /tmp/streaming.log
```

### Monitor Spark Jobs

```bash
# Open Spark Web UI
# http://localhost:8080

# Check running applications via CLI
docker exec spark-master curl -s http://localhost:8080/json/ | python3 -m json.tool
```

---

## 📨 Kafka Operations

### List Topics

```bash
# List all topics
docker exec kafka kafka-topics --bootstrap-server kafka:9092 --list

# List with details
docker exec kafka kafka-topics --bootstrap-server kafka:9092 --describe
```

### Check Message Counts

```bash
# Count messages in all topics
for topic in energy traffic bus_gps waste emergency; do
  count=$(docker exec kafka kafka-run-class kafka.tools.GetOffsetShell \
    --broker-list kafka:9092 --topic $topic 2>/dev/null | awk -F: '{sum+=$3} END{print sum}')
  echo "$topic: $count messages"
done
```

**Alternative (per partition)**:
```bash
# Detailed message count per partition
docker exec kafka kafka-run-class kafka.tools.GetOffsetShell \
  --broker-list kafka:9092 --topic energy
```

### View Sample Messages

```bash
# Energy data (first 3 messages)
docker exec kafka kafka-console-consumer --bootstrap-server kafka:9092 \
  --topic energy --from-beginning --max-messages 3

# Traffic data (live stream)
docker exec kafka kafka-console-consumer --bootstrap-server kafka:9092 \
  --topic traffic --max-messages 5

# All topics (1 message each)
for topic in energy traffic bus_gps waste emergency; do
  echo "=== $topic ==="
  docker exec kafka kafka-console-consumer --bootstrap-server kafka:9092 \
    --topic $topic --from-beginning --max-messages 1 --timeout-ms 3000 2>/dev/null
done
```

### Topic Management

**Delete Topic:**
```bash
docker exec kafka kafka-topics --bootstrap-server kafka:9092 --delete --topic <topic-name>
```

**Delete All Topics (Reset):**
```bash
for topic in energy traffic bus_gps waste emergency; do
  docker exec kafka kafka-topics --bootstrap-server kafka:9092 --delete --topic $topic
done
```

**Recreate Topics:**
```bash
for topic in energy traffic bus_gps waste emergency; do
  docker exec kafka kafka-topics --bootstrap-server kafka:9092 \
    --create --topic $topic --partitions 3 --replication-factor 1
done
```

### Consumer Groups

```bash
# List consumer groups
docker exec kafka kafka-consumer-groups --bootstrap-server kafka:9092 --list

# Describe specific group
docker exec kafka kafka-consumer-groups --bootstrap-server kafka:9092 \
  --group <group-id> --describe
```

---

## 💾 HDFS Operations

### Check Cluster Status

```bash
# Full HDFS report
docker exec namenode hdfs dfsadmin -report

# Summary only (first 20 lines)
docker exec namenode hdfs dfsadmin -report | head -20
```

### List SmartCity Data

```bash
# List top-level directories
docker exec namenode hdfs dfs -ls /smartcity/

# Recursive listing (all files)
docker exec namenode hdfs dfs -ls -R /smartcity/

# First 30 files only
docker exec namenode hdfs dfs -ls -R /smartcity/ | head -30
```

### Check Storage Usage

```bash
# Human-readable storage per directory
docker exec namenode hdfs dfs -du -h /smartcity/

# Detailed breakdown
docker exec namenode hdfs dfs -du -h -s /smartcity/*
```

**Expected output:**
```
116.7 K  350.1 K  /smartcity/bus_gps
134.0 K  402.0 K  /smartcity/emergency
120.7 K  362.2 K  /smartcity/energy
0        0        /smartcity/models
96.0 K   288.1 K  /smartcity/traffic
96.2 K   288.6 K  /smartcity/waste
```

### Count Parquet Files

```bash
# Count files per topic
for topic in energy traffic bus_gps waste emergency; do
  count=$(docker exec namenode hdfs dfs -ls -R /smartcity/$topic/ 2>/dev/null | grep -c "\.parquet")
  echo "$topic: $count parquet files"
done
```

### Read Parquet Files

```bash
# Sample data using Spark
docker exec spark-notebook bash -c "spark-submit --master local \
  /tmp/read_parquet_sample.py /smartcity/energy/"
```

### File Operations

**Copy from HDFS to local:**
```bash
docker exec namenode hdfs dfs -get /smartcity/energy/ingestion_date=2025-11-29/ ./local-data/
```

**Copy from local to HDFS:**
```bash
docker cp ./local-file.txt namenode:/tmp/
docker exec namenode hdfs dfs -put /tmp/local-file.txt /smartcity/
```

**Delete files:**
```bash
# Delete specific directory
docker exec namenode hdfs dfs -rm -r /smartcity/energy/old-data/

# Delete all data (CAREFUL!)
docker exec namenode hdfs dfs -rm -r -f /smartcity/*
```

### Reset HDFS (Complete Wipe)

```bash
# ⚠️ DESTRUCTIVE: Delete all smartcity data and recreate structure
docker exec namenode hdfs dfs -rm -r -f /smartcity
docker exec namenode hdfs dfs -mkdir -p /smartcity/{energy,traffic,bus_gps,waste,emergency,models}
docker exec namenode hdfs dfs -chmod -R 777 /smartcity

echo "✅ HDFS reset complete"
```

### HDFS Safe Mode

```bash
# Check safe mode status
docker exec namenode hdfs dfsadmin -safemode get

# Leave safe mode (if stuck)
docker exec namenode hdfs dfsadmin -safemode leave

# Force enter safe mode (for maintenance)
docker exec namenode hdfs dfsadmin -safemode enter
```

---

## 🤖 ML Model Training

### Copy Scripts to spark-notebook

```bash
# Copy all ML scripts
for f in ml_energy_prediction.py ml_traffic_prediction.py ml_bus_prediction.py \
         ml_waste_prediction.py ml_emergency_prediction.py; do
  docker cp scripts/$f spark-notebook:/home/jovyan/
done

# Verify files copied
docker exec spark-notebook ls -lh /home/jovyan/ml_*.py
```

### Train Individual Models

**Energy Prediction Model:**
```bash
docker exec spark-notebook bash -c "HADOOP_USER_NAME=root spark-submit \
  --master local[*] --conf spark.hadoop.fs.defaultFS=hdfs://namenode:9000 \
  /home/jovyan/ml_energy_prediction.py"
```
> ⏱️ **Duration**: 2-3 minutes | **Output**: R²=0.62, RMSE=9.75 kWh

**Traffic Prediction Model:**
```bash
docker exec spark-notebook bash -c "HADOOP_USER_NAME=root spark-submit \
  --master local[*] --conf spark.hadoop.fs.defaultFS=hdfs://namenode:9000 \
  /home/jovyan/ml_traffic_prediction.py"
```

**Bus Prediction Model:**
```bash
docker exec spark-notebook bash -c "HADOOP_USER_NAME=root spark-submit \
  --master local[*] --conf spark.hadoop.fs.defaultFS=hdfs://namenode:9000 \
  /home/jovyan/ml_bus_prediction.py"
```

**Waste Prediction Model:**
```bash
docker exec spark-notebook bash -c "HADOOP_USER_NAME=root spark-submit \
  --master local[*] --conf spark.hadoop.fs.defaultFS=hdfs://namenode:9000 \
  /home/jovyan/ml_waste_prediction.py"
```

**Emergency Prediction Model:**
```bash
docker exec spark-notebook bash -c "HADOOP_USER_NAME=root spark-submit \
  --master local[*] --conf spark.hadoop.fs.defaultFS=hdfs://namenode:9000 \
  /home/jovyan/ml_emergency_prediction.py"
```

### Train All Models (Automated)

```bash
# Train all 5 models sequentially
for model in energy traffic bus waste emergency; do
  echo "=== Training $model model ==="
  docker exec spark-notebook bash -c "HADOOP_USER_NAME=root timeout 120 spark-submit \
    --master local[*] --conf spark.hadoop.fs.defaultFS=hdfs://namenode:9000 \
    /home/jovyan/ml_${model}_prediction.py" 2>&1 | tail -20
  echo ""
done

echo "✅ All models trained!"
```

> ⏱️ **Total Duration**: ~10-15 minutes for all 5 models

### Verify Models Saved

```bash
# Check models in HDFS
docker exec namenode hdfs dfs -ls -R /smartcity/models/

# Expected: 5 model directories
```

---

## 📊 Monitoring

### Check All Container Status

```bash
# Simple format
docker-compose ps

# Table format with ports
docker-compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"

# Only running containers
docker-compose ps --filter "status=running"
```

### View Container Logs

```bash
# Kafka logs (last 50 lines)
docker logs kafka --tail 50

# Spark Master logs (follow live)
docker logs spark-master -f

# HDFS NameNode logs
docker logs namenode --tail 50

# All Airflow services
docker logs data-pipeline-compose-airflow-webserver-1 --tail 30
docker logs data-pipeline-compose-airflow-scheduler-1 --tail 30
```

### Resource Usage

```bash
# Current resource usage (snapshot)
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"

# Live monitoring (updates every 2 seconds)
docker stats

# Specific container only
docker stats spark-master --no-stream
```

### Disk Usage

```bash
# Docker disk usage
docker system df

# Detailed breakdown
docker system df -v

# Clean up unused resources (CAREFUL!)
docker system prune -a --volumes
```

### Health Checks

```bash
# Check healthy containers
docker ps --filter "health=healthy"

# Check unhealthy containers (troubleshoot these!)
docker ps --filter "health=unhealthy"

# Inspect specific container health
docker inspect --format='{{.State.Health.Status}}' <container-name>
```

### Web Dashboards

Open these URLs in your browser:

```bash
# Spark Master: Monitor jobs and workers
open http://localhost:8080  # macOS
# or
xdg-open http://localhost:8080  # Linux
# or navigate manually to http://localhost:8080

# HDFS NameNode: Browse files
open http://localhost:9870

# Jupyter Notebook: Data exploration
open http://localhost:8888

# Airflow: Workflow monitoring
open http://localhost:8082
```

---

## 🔄 Airflow Operations

### Check Airflow Status

```bash
# Check scheduler health via API
curl -s http://localhost:8082/health | python3 -m json.tool

# List all DAGs
docker exec -u airflow data-pipeline-compose-airflow-webserver-1 \
  airflow dags list
```

### Manage DAGs

**Unpause DAG:**
```bash
docker exec -u airflow data-pipeline-compose-airflow-webserver-1 \
  airflow dags unpause smartcity_pipeline
```

**Pause DAG:**
```bash
docker exec -u airflow data-pipeline-compose-airflow-webserver-1 \
  airflow dags pause smartcity_pipeline
```

**Trigger Manual Run:**
```bash
docker exec -u airflow data-pipeline-compose-airflow-webserver-1 \
  airflow dags trigger smartcity_pipeline
```

**Trigger with specific date:**
```bash
docker exec -u airflow data-pipeline-compose-airflow-webserver-1 \
  airflow dags trigger smartcity_pipeline --exec-date 2025-11-29
```

### Check DAG Runs

```bash
# List all runs for smartcity_pipeline
docker exec -u airflow data-pipeline-compose-airflow-webserver-1 \
  airflow dags list-runs -d smartcity_pipeline

# Show only recent runs
docker exec -u airflow data-pipeline-compose-airflow-webserver-1 \
  airflow dags list-runs -d smartcity_pipeline --num-runs 5
```

**Check specific run tasks:**
```bash
docker exec -u airflow data-pipeline-compose-airflow-webserver-1 \
  airflow tasks states-for-dag-run smartcity_pipeline '<run_id>'
```

### View Task Logs

**Via Airflow UI:**
- Navigate to http://localhost:8082
- Click on DAG → Run → Task → Logs

**Via CLI:**
```bash
# List log directories
ls -la airflow/logs/dag_id=smartcity_pipeline/

# View specific task log
docker exec -u airflow data-pipeline-compose-airflow-webserver-1 \
  airflow tasks logs smartcity_pipeline check_kafka_connection 2025-11-29
```

### Fix Airflow Network Issues

```bash
# Connect all Airflow services to required networks
for svc in webserver scheduler worker triggerer; do
  docker network connect data-pipeline-compose_kafka-net data-pipeline-compose-airflow-$svc-1 2>/dev/null
  docker network connect data-pipeline-compose_default data-pipeline-compose-airflow-$svc-1 2>/dev/null
done

# Restart Airflow scheduler and worker
docker restart data-pipeline-compose-airflow-scheduler-1 \
  data-pipeline-compose-airflow-worker-1

echo "✅ Airflow networks fixed. Wait 30 seconds for services to restart."
```

### Reset Airflow Database

```bash
# ⚠️ DESTRUCTIVE: Wipes all DAG run history
docker exec -u airflow data-pipeline-compose-airflow-webserver-1 \
  airflow db reset --yes

# Reinitialize database
docker exec -u airflow data-pipeline-compose-airflow-webserver-1 \
  airflow db init
```

---

## 🔧 Troubleshooting

### Reset Everything

```bash
# Complete system reset (⚠️ DESTRUCTIVE)
docker-compose down -v
docker-compose up -d
sleep 120  # Wait for services to start

# Run setup again
./setup.sh  # Or manual setup commands
```

### Fix Network Connectivity

**Spark to Kafka:**
```bash
docker network connect data-pipeline-compose_kafka-net spark-master
docker network connect data-pipeline-compose_kafka-net spark-notebook

# Verify
docker exec spark-master ping -c 2 kafka
```

**Spark to HDFS:**
```bash
docker network connect data-pipeline-compose_default spark-notebook

# Verify
docker exec spark-notebook ping -c 2 namenode
```

**Complete Network Fix:**
```bash
# Connect all necessary networks
docker network connect data-pipeline-compose_kafka-net spark-master
docker network connect data-pipeline-compose_kafka-net spark-notebook
docker network connect data-pipeline-compose_default spark-notebook

for svc in webserver scheduler worker triggerer; do
  docker network connect data-pipeline-compose_kafka-net data-pipeline-compose-airflow-$svc-1 2>/dev/null
  docker network connect data-pipeline-compose_default data-pipeline-compose-airflow-$svc-1 2>/dev/null
done

echo "✅ All networks connected"
```

### Check Kafka Connectivity

```bash
# Test Kafka connection from Spark
docker exec spark-master python3 -c "
from kafka import KafkaProducer
import json
try:
    producer = KafkaProducer(bootstrap_servers=['kafka:9092'], request_timeout_ms=5000)
    producer.send('energy', b'test')
    producer.flush()
    print('✅ Kafka connection OK')
except Exception as e:
    print(f'❌ Kafka connection failed: {e}')
"
```

### Check HDFS Connectivity

```bash
# Test namenode reachability
docker exec spark-notebook python3 -c "
import socket
try:
    socket.gethostbyname('namenode')
    print('✅ HDFS namenode reachable')
except Exception as e:
    print(f'❌ Cannot reach namenode: {e}')
"

# Test HDFS write permission
docker exec namenode hdfs dfs -touchz /smartcity/test_write.txt
docker exec namenode hdfs dfs -rm /smartcity/test_write.txt
echo "✅ HDFS write test passed"
```

### View Spark Job Logs

```bash
# Streaming logs
docker exec spark-master cat /tmp/streaming.log

# Last 100 lines
docker exec spark-master tail -100 /tmp/streaming.log

# Search for errors
docker exec spark-master grep -i "error\|exception\|failed" /tmp/streaming.log
```

### HDFS Safe Mode Issues

```bash
# Check safe mode status
docker exec namenode hdfs dfsadmin -safemode get

# Leave safe mode if stuck
docker exec namenode hdfs dfsadmin -safemode leave

# Wait for safe mode to exit automatically (check every 10s)
while docker exec namenode hdfs dfsadmin -safemode get | grep -q ON; do
  echo "Waiting for safe mode to exit..."
  sleep 10
done
echo "✅ HDFS is out of safe mode"
```

### Container Won't Start

```bash
# Check container logs for errors
docker logs <container-name> --tail 100

# Check if port is already in use
netstat -tulpn | grep <port-number>  # Linux
lsof -i :<port-number>  # macOS

# Force recreate specific container
docker-compose up -d --force-recreate <service-name>
```

### Out of Memory Issues

```bash
# Check current memory usage
docker stats --no-stream

# Increase Docker memory limit (Docker Desktop)
# Settings → Resources → Memory → Increase to 16GB

# Restart with memory limits
docker-compose down
docker-compose up -d --scale spark-worker=1  # Reduce workers if needed
```

### Clean Up Disk Space

```bash
# Remove stopped containers
docker container prune -f

# Remove unused images
docker image prune -a -f

# Remove unused volumes (⚠️ CAREFUL - deletes data!)
docker volume prune -f

# Complete cleanup (⚠️ VERY DESTRUCTIVE)
docker system prune -a --volumes -f
```

### Debug Specific Service

```bash
# Enter container shell
docker exec -it <container-name> bash

# Check environment variables
docker exec <container-name> env

# Check running processes
docker exec <container-name> ps aux

# Check network connectivity
docker exec <container-name> ping kafka
docker exec <container-name> ping namenode
docker exec <container-name> curl http://localhost:8080
```

### Restart Individual Services

```bash
# Restart specific container
docker restart <container-name>

# Restart multiple containers
docker restart kafka namenode spark-master

# Restart all Spark services
docker restart spark-master spark-worker-1 spark-worker-2 spark-notebook
```

---

## 📋 Command Categories

### Container Management
```bash
docker-compose up -d                    # Start all
docker-compose down                     # Stop all
docker-compose restart                  # Restart all
docker-compose ps                       # Check status
docker restart <container>              # Restart one
docker logs <container> -f              # Follow logs
docker exec -it <container> bash        # Enter shell
docker stats                            # Resource usage
```

### Kafka Commands
```bash
kafka-topics --list                     # List topics
kafka-topics --describe                 # Topic details
kafka-console-consumer --topic <name>   # Consume messages
kafka-consumer-groups --list            # List groups
kafka-run-class kafka.tools.GetOffsetShell  # Message counts
```

### HDFS Commands
```bash
hdfs dfs -ls /smartcity/                # List files
hdfs dfs -du -h /smartcity/             # Storage usage
hdfs dfs -mkdir -p /path/               # Create directory
hdfs dfs -rm -r /path/                  # Delete directory
hdfs dfs -get /hdfs/path /local/path    # Download file
hdfs dfs -put /local/path /hdfs/path    # Upload file
hdfs dfsadmin -report                   # Cluster report
hdfs dfsadmin -safemode get             # Check safe mode
```

### Spark Commands
```bash
spark-submit --master local[*] <script> # Submit job
curl http://localhost:8080/json/        # Spark UI JSON
```

### Airflow Commands
```bash
airflow dags list                       # List DAGs
airflow dags trigger <dag_id>           # Trigger DAG
airflow dags unpause <dag_id>           # Unpause DAG
airflow dags list-runs -d <dag_id>      # List runs
airflow tasks logs <dag_id> <task_id>   # View logs
```

---

## 🆘 Getting Help

**Still stuck? Try these resources:**

1. 📖 [README.md](../README.md) - Project overview
2. 🚀 [STARTUP_GUIDE.md](STARTUP_GUIDE.md) - Detailed setup
3. 🏗️ [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture
4. 📊 [DEMO_OUTPUT.md](DEMO_OUTPUT.md) - Expected outputs
5. 🐛 [GitHub Issues](https://github.com/your-repo/issues) - Report bugs

**Quick help commands:**
```bash
# Command help
docker-compose --help
docker exec kafka kafka-topics --help
docker exec namenode hdfs dfs -help

# Service versions
docker --version
docker-compose --version
```

---

<div align="center">

**[⬆ Back to Top](#-command-reference-guide)**

---

**Last Updated**: November 29, 2025 | **Version**: 2.0

</div>
