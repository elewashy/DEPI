import sqlite3
import pandas as pd

def verify_orders():
    """Connects to the database and verifies the orders table."""
    db_path = 'db/orders.db'
    try:
        conn = sqlite3.connect(db_path)
        
        # Check if the table exists
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='orders'")
        if not cursor.fetchone():
            print("The 'orders' table does not exist.")
            return

        print("--- Orders Table Verification ---")
        
        # Display schema
        print("\n--- Schema ---")
        cursor.execute("PRAGMA table_info(orders)")
        schema = cursor.fetchall()
        for col in schema:
            print(f"Column: {col[1]}, Type: {col[2]}, Not Null: {col[3]}, Primary Key: {col[5]}")

        # Display first 10 rows using pandas for better formatting
        print("\n--- First 10 Orders ---")
        df = pd.read_sql_query("SELECT * FROM orders LIMIT 10", conn)
        
        if df.empty:
            print("The 'orders' table is empty.")
        else:
            print(df.to_string())

        # Print total number of orders
        print("\n--- Total Number of Orders ---")
        count = cursor.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
        print(f"Total orders: {count}")

    except sqlite3.Error as e:
        print(f"Database error: {e}")
    except FileNotFoundError:
        print(f"Database file not found at {db_path}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        if 'conn' in locals() and conn:
            conn.close()

if __name__ == "__main__":
    verify_orders()
