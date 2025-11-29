-- Script to list tables and columns from SmartCityDWH
-- Run this after restore to understand the schema

USE SmartCityDWH;
GO

-- List all tables
SELECT 
    s.name AS SchemaName,
    t.name AS TableName,
    p.rows AS RowCounts
FROM sys.tables t
INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
INNER JOIN sys.partitions p ON t.object_id = p.object_id
WHERE p.index_id IN (0, 1)
ORDER BY s.name, t.name;
GO

-- List columns for each table
SELECT 
    t.name AS TableName,
    c.name AS ColumnName,
    ty.name AS DataType,
    c.max_length,
    c.is_nullable
FROM sys.tables t
INNER JOIN sys.columns c ON t.object_id = c.object_id
INNER JOIN sys.types ty ON c.user_type_id = ty.user_type_id
ORDER BY t.name, c.column_id;
GO
