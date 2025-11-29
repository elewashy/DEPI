#!/bin/bash
# Script to restore SmartCityDWH backup in SQL Server

echo "Waiting for SQL Server to start..."
sleep 30

# Restore the database
/opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P 'SmartCity@2024!' -C -Q "
RESTORE DATABASE SmartCityDWH
FROM DISK = '/opt/sql/SmartCityDWH.bak'
WITH MOVE 'SmartCityDWH' TO '/var/opt/mssql/data/SmartCityDWH.mdf',
     MOVE 'SmartCityDWH_log' TO '/var/opt/mssql/data/SmartCityDWH_log.ldf',
     REPLACE
"

echo "Database restore completed!"

# List tables in the restored database
/opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P 'SmartCity@2024!' -C -d SmartCityDWH -Q "
SELECT TABLE_SCHEMA, TABLE_NAME
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_TYPE = 'BASE TABLE'
ORDER BY TABLE_SCHEMA, TABLE_NAME
"
