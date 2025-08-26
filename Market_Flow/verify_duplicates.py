import csv
import glob

def find_duplicates():
    """Checks for duplicate transaction IDs in the transaction files."""
    transaction_files = sorted(glob.glob('data/transactions_*.csv'))
    seen_ids = set()
    duplicates_found = False

    for file in transaction_files:
        with open(file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                transaction_id = row['transaction_id']
                if transaction_id in seen_ids:
                    print(f"Duplicate transaction ID found: {transaction_id} in file {file}")
                    duplicates_found = True
                else:
                    seen_ids.add(transaction_id)
    
    if not duplicates_found:
        print("No duplicate transaction IDs found.")

if __name__ == "__main__":
    find_duplicates()
