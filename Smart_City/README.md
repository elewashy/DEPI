# Smart City Data Warehouse Project

This project demonstrates the construction of a data warehouse for a fictional "Smart City." It showcases three different ETL (Extract, Transform, Load) implementations to populate the data warehouse, each using a different technology stack.

The primary goal is to collect data from various city services (like traffic, energy, waste collection) and model it into a star schema, making it suitable for analytics and business intelligence.

---

## 🎨 Design & Prototyping

The conceptual design and planning for this project can be found on Figma and Canva:

-   **Figma Board:** [Smart City Project on Figma](https://www.figma.com/board/g4Z7tSYQAf4TSLCS85Lnv3/Smart_City?node-id=0-1&t=552hIgLDw6xeHc7n-1)
-   **Canva Design:** [Smart City Project on Canva](https://www.canva.com/design/DAGzeqoUblE/utDSNvIL1xt6Bf1s2339Ug/edit?utm_content=DAGzeqoUblE&utm_campaign=designshare&utm_medium=link2&utm_source=sharebutton)

---

## 📂 Project Structure

The repository is organized into the following main directories:

-   `datasets/`: Contains the source CSV data files used as the raw input for the ETL processes.
-   `docs/`: Contains detailed documentation for each ETL implementation, along with diagrams.
-   `data_with_talend/`: Contains SQL scripts for the source and destination databases used in the Talend ETL jobs.
-   `data_with_sql/`: Implements the entire ETL process using pure T-SQL, following a Medallion Architecture (Bronze, Silver, Gold).
-   `data_with_python/`: Implements the entire ETL process using Python, Pandas, and SQLAlchemy, also following the Medallion Architecture.

---

## 🚀 ETL Implementations

There are three distinct ETL pipelines available in this project.

### 1. Talend ETL

-   **Location:** `data_with_talend/` and `docs/talend_documentation.md`
-   **Description:** A visual ETL process designed in Talend Open Studio. The DDLs for the source (`SmartCity`) and destination (`SmartCityDWH`) databases are provided.
-   **Documentation:** The `talend_documentation.md` file explains the logic of the Talend jobs with screenshots.

### 2. SQL-based ETL (Medallion Architecture)

-   **Location:** `data_with_sql/`
-   **Description:** A pure T-SQL implementation that uses stored procedures to move data through Bronze, Silver, and Gold layers.
-   **How to Run:**
    1.  Execute `init_database.sql` to create the `SmartCityDWH` database and schemas.
    2.  Run the DDL scripts in `bronze/`, `silver/`, and `gold/` to create the tables.
    3.  Execute the stored procedures in order:
        -   `EXEC bronze.load_bronze;`
        -   `EXEC silver.load_silver;`
        -   `EXEC gold.proc_load_gold;`
-   **Documentation:** See `docs/sql_etl_documentation.md` for a detailed breakdown.

### 3. Python-based ETL (Medallion Architecture)

-   **Location:** `data_with_python/`
-   **Description:** A programmatic ETL pipeline using Python, Pandas for data manipulation, and SQLAlchemy for database communication. It replicates the same Bronze, Silver, and Gold logic as the SQL implementation.
-   **How to Run:**
    1.  **Install dependencies:** `pip install -r data_with_python/requirements.txt`
    2.  **Configure DB:** Copy `data_with_python/.env.example` to `.env` and fill in your database credentials.
    3.  **Execute:** Navigate to the `data_with_python` directory and run the main pipeline script:
        ```bash
        python main.py
        ```
-   **Documentation:** See `docs/python_etl_documentation.md` for a detailed breakdown.

---

##  orchestrations

There are four distinct ETL pipelines available in this project.

### 4. Airflow Orchestration for Talend Jobs

-   **Location:** `Smart_City_Airflow/`
-   **Description:** An Apache Airflow setup to orchestrate and schedule the execution of the exported Talend jobs. It dynamically generates a DAG for each Talend job found in its directory.
-   **How to Use:**
    1.  Export your Talend jobs as standalone executables.
    2.  Place the `Smart_City_Airflow` folder inside your Airflow `dags` directory.
    3.  Airflow will automatically create and manage a DAG for each job.
-   **Documentation:** See `docs/airflow_orchestration.md` for a detailed breakdown.
