import csv
import random
from datetime import datetime, timedelta
import os
import sqlite3

def get_last_transaction_id():
    """Fetches the last transaction ID from the orders database."""
    try:
        conn = sqlite3.connect('db/orders.db')
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(transaction_id) FROM orders")
        last_id = cursor.fetchone()[0]
        conn.close()
        return last_id or 0
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return 0

def generate_new_transactions(num_transactions=3000, start_transaction_id=12001, file_index=13):
    """Generates a new CSV file with transaction data."""
    product_ids = list(range(1, 101))
    branches = ['Cairo', 'Alexandria', 'Giza', 'Luxor', 'Aswan']
    start_date = datetime.now()

    file_name = f'data/transactions_{file_index}.csv'
    with open(file_name, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['transaction_id', 'customer_id', 'product_id', 'quantity', 'transaction_date', 'branch'])
        for i in range(num_transactions):
            transaction_id = start_transaction_id + i
            customer_id = random.randint(1, 2000)
            product_id = random.choice(product_ids)
            quantity = random.randint(1, 5)
            transaction_date = start_date + timedelta(seconds=random.randint(0, 24*60*60))
            branch = random.choice(branches)
            writer.writerow([transaction_id, customer_id, product_id, quantity, transaction_date.strftime('%Y-%m-%d %H:%M:%S'), branch])

def main():
    """Main function to generate new transaction data."""
    os.makedirs('data', exist_ok=True)
    
    last_id = get_last_transaction_id()
    start_id = last_id + 1
    file_idx = (last_id // 1000) + 1

    print(f"Generating new transactions starting from ID {start_id} into file transactions_{file_idx}.csv...")
    generate_new_transactions(start_transaction_id=start_id, file_index=file_idx)
    print("New transactions generated successfully.")

if __name__ == "__main__":
    main()
