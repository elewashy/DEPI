import json
import csv
import sqlite3
import glob
from currency_conversion import get_usd_to_egp_rate

def create_orders_table(cursor):
    """Creates the orders table in the database if it doesn't exist."""
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS orders (
        transaction_id INTEGER PRIMARY KEY,
        product_id INTEGER,
        quantity INTEGER,
        product_name TEXT,
        amount REAL,
        customer_full_name TEXT,
        transaction_date TEXT,
        branch TEXT,
        transaction_date_key INTEGER
    )
    ''')

def create_indexes(cursor):
    """Creates indexes on the orders table for performance."""
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_transaction_id ON orders (transaction_id);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_product_id ON orders (product_id);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_transaction_date ON orders (transaction_date);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_transaction_date_key ON orders (transaction_date_key);')

def etl_pipeline():
    """
    Main ETL pipeline to process data from JSON, CSV, and a database,
    and load it into an 'orders' table.
    """
    try:
        # --- Connect to Databases ---
        customer_db_conn = sqlite3.connect('db/customers.db')
        customer_cursor = customer_db_conn.cursor()

        orders_db_conn = sqlite3.connect('db/orders.db')
        orders_cursor = orders_db_conn.cursor()

        # --- Create orders table ---
        create_orders_table(orders_cursor)
        create_indexes(orders_cursor)
        
        # --- Get Exchange Rate ---
        exchange_rate = get_usd_to_egp_rate()

        # --- Load Products ---
        with open('data/products.json', 'r') as f:
            products = {p['id']: p for p in json.load(f)}

        # --- Process Transactions ---
        transaction_files = sorted(glob.glob('data/transactions_*.csv'))
        processed_ids = set()

        for file in transaction_files:
            with open(file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        transaction_id = int(row['transaction_id'])
                        if transaction_id in processed_ids:
                            continue
                        
                        # 1. Get Product Info
                        product_id = int(row['product_id'])
                        product_info = products.get(product_id)
                        
                        if not product_info:
                            print(f"Warning: Product with ID {product_id} not found. Skipping transaction {row['transaction_id']}.")
                            continue
                            
                        product_name = product_info['name']
                        price_usd = product_info['price']
                        quantity = int(row['quantity'])
                        # Convert amount to EGP before inserting
                        amount_egp = round((price_usd * quantity) * exchange_rate, 2)

                        # 2. Get Customer Info
                        customer_id = int(row['customer_id'])
                        customer_cursor.execute("SELECT first_name, last_name FROM customers WHERE id=?", (customer_id,))
                        customer_data = customer_cursor.fetchone()
                        customer_full_name = f"{customer_data[0]} {customer_data[1]}" if customer_data else "Unknown"
                        transaction_date = row['transaction_date']
                        # Extract only the date part and format as YYYYMMDD
                        transaction_date_key = int(transaction_date.split(' ')[0].replace('-', ''))

                        # 3. Insert into orders table
                        orders_cursor.execute("""
                        INSERT INTO orders (transaction_id, product_id, quantity, product_name, amount, customer_full_name, transaction_date, branch, transaction_date_key)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            transaction_id,
                            product_id,
                            quantity,
                            product_name,
                            amount_egp, # Use the converted amount
                            customer_full_name,
                            transaction_date,
                            row['branch'],
                            transaction_date_key
                        ))
                        processed_ids.add(transaction_id)
                    except (ValueError, KeyError) as e:
                        print(f"Error processing row: {row}. Error: {e}. Skipping.")
                        continue

        # --- Commit and Close Connections ---
        orders_db_conn.commit()
        print("ETL pipeline completed successfully! Orders table is ready.")

    except sqlite3.Error as e:
        print(f"Database error: {e}")
    except FileNotFoundError as e:
        print(f"File not found: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        if 'customer_db_conn' in locals() and customer_db_conn:
            customer_db_conn.close()
        if 'orders_db_conn' in locals() and orders_db_conn:
            orders_db_conn.close()

if __name__ == "__main__":
    etl_pipeline()


