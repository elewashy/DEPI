import csv
import random
from datetime import datetime, timedelta
import sqlite3

def get_existing_transaction_ids(sample_size=500):
    """Fetches a random sample of existing transaction IDs from the orders database."""
    try:
        conn = sqlite3.connect('db/orders.db')
        cursor = conn.cursor()
        cursor.execute("SELECT transaction_id FROM orders")
        ids = [row[0] for row in cursor.fetchall()]
        conn.close()
        return random.sample(ids, min(len(ids), sample_size))
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return []

def generate_mixed_transactions(num_new=2500, file_index=14):
    """Generates a CSV file with a mix of new and updated transaction data."""
    last_id = get_last_transaction_id()
    start_id = last_id + 1

    updated_ids = get_existing_transaction_ids()
    
    product_ids = list(range(1, 101))
    branches = ['Cairo', 'Alexandria', 'Giza', 'Luxor', 'Aswan']
    start_date = datetime.now()

    file_name = f'data/transactions_{file_index}.csv'
    with open(file_name, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['transaction_id', 'customer_id', 'product_id', 'quantity', 'transaction_date', 'branch'])
        
        # Add new transactions
        for i in range(num_new):
            transaction_id = start_id + i
            customer_id = random.randint(1, 2000)
            product_id = random.choice(product_ids)
            quantity = random.randint(1, 5)
            transaction_date = start_date + timedelta(seconds=random.randint(0, 24*60*60))
            branch = random.choice(branches)
            writer.writerow([transaction_id, customer_id, product_id, quantity, transaction_date.strftime('%Y-%m-%d %H:%M:%S'), branch])

        # Add updated transactions
        for transaction_id in updated_ids:
            customer_id = random.randint(1, 2000)
            product_id = random.choice(product_ids)
            quantity = random.randint(1, 10) # Potentially updated quantity
            transaction_date = start_date + timedelta(seconds=random.randint(0, 24*60*60))
            branch = random.choice(branches)
            writer.writerow([transaction_id, customer_id, product_id, quantity, transaction_date.strftime('%Y-%m-%d %H:%M:%S'), branch])

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

def main():
    """Main function to generate mixed transaction data."""
    print("Generating mixed transactions...")
    generate_mixed_transactions()
    print("Mixed transactions generated successfully.")

if __name__ == "__main__":
    main()
