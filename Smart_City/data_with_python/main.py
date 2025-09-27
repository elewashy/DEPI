from bronze.load_bronze import load_bronze_layer
from silver.load_silver import load_silver_layer
from gold.load_gold import load_gold_layer
import time

def main():
    """
    Orchestrates the entire ETL process by running the load scripts for each layer in sequence.
    """
    print("================================================")
    print("Starting Full ETL Pipeline")
    print("================================================")
    
    pipeline_start_time = time.time()

    # Run Bronze Layer ETL
    load_bronze_layer()

    # Run Silver Layer ETL
    load_silver_layer()

    # Run Gold Layer ETL
    load_gold_layer()

    pipeline_end_time = time.time()
    
    print("================================================")
    print("Full ETL Pipeline Completed Successfully!")
    print(f"   - Total Pipeline Duration: {pipeline_end_time - pipeline_start_time:.2f} seconds")
    print("================================================")


if __name__ == '__main__':
    main()
