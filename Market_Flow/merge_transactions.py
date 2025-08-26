import json
import csv
import sqlite3
import glob
import os
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

def merge_transactions():
    """
    Processes a transaction file with mixed new and updated data,
    and merges it into the 'orders' table.
    """
    try:
        # --- Connect to Databases ---
        customer_db_conn = sqlite3.connect('db/customers.db')
        customer_cursor = customer_db_conn.cursor()

        orders_db_conn = sqlite3.connect('db/orders.db')
        orders_cursor = orders_db_conn.cursor()

        # --- Create table and indexes ---
        create_orders_table(orders_cursor)
        create_indexes(orders_cursor)
        
        # --- Get Exchange Rate ---
        exchange_rate = get_usd_to_egp_rate()

        # --- Load Products ---
        with open('data/products.json', 'r') as f:
            products = {p['id']: p for p in json.load(f)}

        # --- Process Mixed Transaction File ---
        # Find the latest transaction file to process for the merge.
        transaction_files = glob.glob('data/transactions_*.csv')
        if not transaction_files:
            print("No transaction files found.")
            return
            
        mixed_data_file = max(transaction_files, key=os.path.getmtime)
        print(f"Processing merge for file: {mixed_data_file}")
        
        updates = 0
        inserts = 0

        with open(mixed_data_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    # 1. Get Product Info
                    product_id = int(row['product_id'])
                    product_info = products.get(product_id)
                    
                    if not product_info:
                        print(f"Warning: Product with ID {product_id} not found. Skipping transaction {row['transaction_id']}.")
                        continue
                        
                    product_name = product_info['name']
                    price_usd = product_info['price']
                    quantity = int(row['quantity'])
                    # Convert amount to EGP before inserting/updating
                    amount_egp = round((price_usd * quantity) * exchange_rate, 2)

                    # 2. Get Customer Info
                    customer_id = int(row['customer_id'])
                    customer_cursor.execute("SELECT first_name, last_name FROM customers WHERE id=?", (customer_id,))
                    customer_data = customer_cursor.fetchone()
                    customer_full_name = f"{customer_data[0]} {customer_data[1]}" if customer_data else "Unknown"
                    transaction_date = row['transaction_date']
                    # Extract only the date part and format as YYYYMMDD
                    transaction_date_key = int(transaction_date.split(' ')[0].replace('-', ''))

                    # 3. Merge into orders table
                    orders_cursor.execute("""
                    INSERT INTO orders (transaction_id, product_id, quantity, product_name, amount, customer_full_name, transaction_date, branch, transaction_date_key)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(transaction_id) DO UPDATE SET
                        product_id = excluded.product_id,
                        quantity = excluded.quantity,
                        product_name = excluded.product_name,
                        amount = excluded.amount,
                        customer_full_name = excluded.customer_full_name,
                        transaction_date = excluded.transaction_date,
                        branch = excluded.branch,
                        transaction_date_key = excluded.transaction_date_key
                    """, (
                        row['transaction_id'],
                        product_id,
                        quantity,
                        product_name,
                        amount_egp, # Use the converted amount
                        customer_full_name,
                        transaction_date,
                        row['branch'],
                        transaction_date_key
                    ))
                    
                    if orders_cursor.rowcount > 0:
                        # This is a bit tricky: INSERT OR REPLACE would give a rowcount, but ON CONFLICT might not.
                        # A better way is to check if the ID existed before.
                        # For this simulation, we'll just count. A real scenario might need pre-checking.
                        pass

                except (ValueError, KeyError) as e:
                    print(f"Error processing row: {row}. Error: {e}. Skipping.")
                    continue
        
        # A simple way to get counts after the fact
        # This is not perfectly accurate for the merge itself but gives a good idea
        orders_cursor.execute("SELECT MAX(transaction_id) FROM orders")
        max_id_after_merge = orders_cursor.fetchone()[0]
        
        # Let's assume we know the max_id before we started.
        # This is a simplification for this script.
        # In a real pipeline, you'd track this state.
        
        print("Merge operation completed.")
        # We can't easily tell inserts vs updates from the cursor in SQLite this way.
        # A more complex approach would be needed for precise counts.

        # --- Commit and Close Connections ---
        orders_db_conn.commit()

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
    merge_transactions()
