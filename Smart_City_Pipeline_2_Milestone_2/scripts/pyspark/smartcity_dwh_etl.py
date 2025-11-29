"""
SmartCity DWH ETL Pipeline
Extracts data from SQL Server (SmartCityDWH) and loads into Hive tables
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import current_timestamp, lit
import sys

# SQL Server connection details
SQLSERVER_HOST = "sqlserver"
SQLSERVER_PORT = "1433"
SQLSERVER_DB = "SmartCityDWH"
SQLSERVER_USER = "sa"
SQLSERVER_PASSWORD = "SmartCity@2024!"
JDBC_URL = f"jdbc:sqlserver://{SQLSERVER_HOST}:{SQLSERVER_PORT};databaseName={SQLSERVER_DB};encrypt=false;trustServerCertificate=true"

# HDFS and Hive settings
HIVE_DATABASE = "smartcity_dwh"
HDFS_WAREHOUSE = "hdfs://namenode:9000/user/hive/warehouse"


def create_spark_session():
    """Create SparkSession with Hive support and SQL Server JDBC driver"""
    return SparkSession.builder \
        .appName("SmartCityDWH_ETL") \
        .config("spark.master", "spark://spark-master:7077") \
        .config("spark.sql.warehouse.dir", HDFS_WAREHOUSE) \
        .config("spark.hadoop.fs.defaultFS", "hdfs://namenode:9000") \
        .config("hive.metastore.uris", "thrift://hive-metastore:9083") \
        .config("spark.sql.catalogImplementation", "hive") \
        .config("spark.jars", "/opt/spark/jars/mssql-jdbc-12.4.2.jre8.jar") \
        .enableHiveSupport() \
        .getOrCreate()


def get_sqlserver_tables(spark):
    """Get list of tables from SQL Server database"""
    query = """
    (SELECT TABLE_SCHEMA, TABLE_NAME 
     FROM INFORMATION_SCHEMA.TABLES 
     WHERE TABLE_TYPE = 'BASE TABLE') AS tables
    """
    
    df = spark.read \
        .format("jdbc") \
        .option("url", JDBC_URL) \
        .option("dbtable", query) \
        .option("user", SQLSERVER_USER) \
        .option("password", SQLSERVER_PASSWORD) \
        .option("driver", "com.microsoft.sqlserver.jdbc.SQLServerDriver") \
        .load()
    
    return [(row.TABLE_SCHEMA, row.TABLE_NAME) for row in df.collect()]


def extract_table(spark, schema, table_name):
    """Extract a table from SQL Server"""
    full_table_name = f"{schema}.{table_name}"
    print(f"Extracting table: {full_table_name}")
    
    df = spark.read \
        .format("jdbc") \
        .option("url", JDBC_URL) \
        .option("dbtable", full_table_name) \
        .option("user", SQLSERVER_USER) \
        .option("password", SQLSERVER_PASSWORD) \
        .option("driver", "com.microsoft.sqlserver.jdbc.SQLServerDriver") \
        .load()
    
    # Add ETL metadata columns
    df = df.withColumn("_etl_timestamp", current_timestamp()) \
           .withColumn("_source_schema", lit(schema)) \
           .withColumn("_source_table", lit(table_name))
    
    return df


def create_hive_database(spark):
    """Create the Hive database if it doesn't exist"""
    spark.sql(f"CREATE DATABASE IF NOT EXISTS {HIVE_DATABASE}")
    spark.sql(f"USE {HIVE_DATABASE}")
    print(f"Using Hive database: {HIVE_DATABASE}")


def load_to_hive(df, table_name, mode="overwrite"):
    """Load DataFrame to Hive table"""
    # Sanitize table name for Hive
    hive_table = table_name.lower().replace(" ", "_").replace("-", "_")
    full_table = f"{HIVE_DATABASE}.{hive_table}"
    
    print(f"Loading to Hive table: {full_table}")
    print(f"Record count: {df.count()}")
    
    df.write \
        .mode(mode) \
        .format("parquet") \
        .option("path", f"{HDFS_WAREHOUSE}/{HIVE_DATABASE}.db/{hive_table}") \
        .saveAsTable(full_table)
    
    print(f"Successfully loaded {full_table}")


def run_etl(tables_filter=None):
    """Run the full ETL process"""
    spark = None
    try:
        print("=" * 60)
        print("Starting SmartCity DWH ETL Pipeline")
        print("=" * 60)
        
        # Create Spark session
        spark = create_spark_session()
        spark.sparkContext.setLogLevel("WARN")
        
        # Create Hive database
        create_hive_database(spark)
        
        # Get list of tables from SQL Server
        tables = get_sqlserver_tables(spark)
        print(f"Found {len(tables)} tables in SQL Server")
        
        # Apply filter if provided
        if tables_filter:
            tables = [(s, t) for s, t in tables if t.lower() in [f.lower() for f in tables_filter]]
            print(f"Filtered to {len(tables)} tables")
        
        # Process each table
        success_count = 0
        error_count = 0
        
        for schema, table_name in tables:
            try:
                # Extract from SQL Server
                df = extract_table(spark, schema, table_name)
                
                # Load to Hive
                hive_name = f"{schema}_{table_name}" if schema.lower() != "dbo" else table_name
                load_to_hive(df, hive_name)
                
                success_count += 1
                
            except Exception as e:
                print(f"Error processing {schema}.{table_name}: {str(e)}")
                error_count += 1
        
        print("=" * 60)
        print(f"ETL Complete: {success_count} succeeded, {error_count} failed")
        print("=" * 60)
        
        # Show Hive tables created
        spark.sql(f"SHOW TABLES IN {HIVE_DATABASE}").show(100, truncate=False)
        
        return 0 if error_count == 0 else 1
        
    except Exception as e:
        print(f"ETL Pipeline Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
        
    finally:
        if spark:
            spark.stop()


if __name__ == "__main__":
    # Optional: pass table names as arguments to filter
    tables_filter = sys.argv[1:] if len(sys.argv) > 1 else None
    exit_code = run_etl(tables_filter)
    sys.exit(exit_code)
