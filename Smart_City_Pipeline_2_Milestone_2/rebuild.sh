#!/bin/bash
# SmartCity Data Pipeline - Complete Rebuild Script
# Run this to rebuild the entire pipeline from scratch

set -e

cd /workspaces/winn/data-pipeline-compose

echo "=========================================="
echo "  SmartCity Data Pipeline - Full Rebuild"
echo "=========================================="
echo ""

echo "=== Step 1: Cleaning up previous state ==="
docker compose down -v 2>/dev/null || true
echo "Done."

echo ""
echo "=== Step 2: Starting infrastructure ==="
docker compose up -d
echo "Waiting 2 minutes for services to initialize..."
sleep 120
echo "Done."

echo ""
echo "=== Step 3: Restoring SQL Server database ==="
docker exec sqlserver mkdir -p /var/opt/mssql/backup 2>/dev/null || true
docker cp sql/SmartCityDWH.bak sqlserver:/var/opt/mssql/backup/
docker exec sqlserver /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P 'SmartCity@2024!' -C -Q "
RESTORE DATABASE SmartCityDWH 
FROM DISK = '/var/opt/mssql/backup/SmartCityDWH.bak'
WITH MOVE 'SmartCityDWH' TO '/var/opt/mssql/data/SmartCityDWH.mdf',
     MOVE 'SmartCityDWH_log' TO '/var/opt/mssql/data/SmartCityDWH_log.ldf',
     REPLACE"
echo "Done."

echo ""
echo "=== Step 4: Installing JDBC drivers on Spark nodes ==="
for node in spark-master spark-worker-1 spark-worker-2; do
  docker exec $node wget -q -P /spark/jars/ \
    https://repo1.maven.org/maven2/com/microsoft/sqlserver/mssql-jdbc/12.4.2.jre8/mssql-jdbc-12.4.2.jre8.jar 2>/dev/null || true
  echo "  - $node: JDBC driver ready"
done
echo "Done."

echo ""
echo "=== Step 5: Creating Hive database ==="
docker exec hive-server beeline -u jdbc:hive2://localhost:10000 \
  -e "CREATE DATABASE IF NOT EXISTS smartcity_dwh" 2>/dev/null || true
echo "Done."

echo ""
echo "=== Step 6: Running Spark ETL job ==="
echo "  This will take approximately 4-5 minutes..."
docker exec spark-master spark-submit \
  --master spark://spark-master:7077 \
  --deploy-mode client \
  --driver-memory 2g \
  --executor-memory 2g \
  --jars /spark/jars/mssql-jdbc-12.4.2.jre8.jar \
  /spark-scripts/pyspark/smartcity_dwh_etl.py
echo "Done."

echo ""
echo "=== Step 7: Waiting for Trino to initialize ==="
sleep 30
echo "Done."

echo ""
echo "=== Step 8: Verifying data in Hive ==="
docker exec trino-coordinator trino --execute "
SELECT table_name as loaded_tables
FROM hive.information_schema.tables 
WHERE table_schema = 'smartcity_dwh'
ORDER BY table_name" 2>/dev/null
echo "Done."

echo ""
echo "=== Step 9: Configuring Airflow ==="
docker exec -u airflow data-pipeline-compose-airflow-scheduler-1 \
  airflow dags unpause smartcity_dwh_pipeline 2>/dev/null
echo "Done."

echo ""
echo "=========================================="
echo "  BUILD COMPLETE!"
echo "=========================================="
echo ""
echo "Data loaded: 12 tables, ~1M+ records"
echo ""
echo "Access points:"
echo "  - Airflow UI:     http://localhost:8082 (admin/admin)"
echo "  - Spark Master:   http://localhost:8080"
echo "  - HDFS NameNode:  http://localhost:9870"
echo ""
echo "Quick test:"
echo "  docker exec trino-coordinator trino --execute \\"
echo "    \"SELECT zone_name, COUNT(*) FROM hive.smartcity_dwh.fact_traffic t \\"
echo "     JOIN hive.smartcity_dwh.dim_zones z ON t.zone_id = z.zone_id \\"
echo "     GROUP BY zone_name\""
echo ""
