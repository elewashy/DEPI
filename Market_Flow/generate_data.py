import json
import csv
import sqlite3
from faker import Faker
import random
from datetime import datetime, timedelta
import os

def generate_products(num_products=100):
    """Generates a list of realistic products."""
    products = []
    product_categories = {
        "Electronics": ["Smartphone", "Laptop", "Tablet", "Headphones", "Smartwatch", "Camera", "Charger", "Power Bank", "Monitor", "Keyboard", "Mouse"],
        "Groceries": ["Milk", "Bread", "Eggs", "Cheese", "Apples", "Bananas", "Tomatoes", "Potatoes", "Chicken", "Beef", "Rice", "Pasta", "Olive Oil", "Coffee", "Tea"],
        "Clothing": ["T-Shirt", "Jeans", "Jacket", "Sweater", "Dress", "Socks", "Shoes", "Hat", "Scarf"],
        "Home Goods": ["Detergent", "Soap", "Shampoo", "Towel", "Light Bulb", "Batteries", "Trash Bags", "Pan", "Plate", "Mug"],
        "Books": ["Fiction Novel", "History Book", "Science Journal", "Cookbook", "Biography", "Poetry Collection"]
    }
    
    brands = ["BrandA", "BrandB", "BrandC", "Super", "Value", "Premium", "Eco"]
    
    generated_products = set()
    product_id = 1
    
    while len(products) < num_products:
        category = random.choice(list(product_categories.keys()))
        item = random.choice(product_categories[category])
        brand = random.choice(brands)
        product_name = f"{brand} {item}"
        
        if product_name not in generated_products:
            price = 0
            if category == "Electronics":
                price = round(random.uniform(150.0, 5000.0), 2)
            elif category == "Groceries":
                price = round(random.uniform(5.0, 150.0), 2)
            elif category == "Clothing":
                price = round(random.uniform(50.0, 700.0), 2)
            elif category == "Home Goods":
                price = round(random.uniform(10.0, 250.0), 2)
            elif category == "Books":
                price = round(random.uniform(40.0, 300.0), 2)

            products.append({
                "id": product_id,
                "name": product_name,
                "price": price
            })
            generated_products.add(product_name)
            product_id += 1
            
    return products

def generate_transactions(products, num_files=12, transactions_per_file=1000):
    """Generates transaction CSV files."""
    product_ids = [p['id'] for p in products]
    branches = ['Cairo', 'Alexandria', 'Giza', 'Luxor', 'Aswan']
    start_date = datetime.now() - timedelta(days=3)

    for i in range(num_files):
        file_name = f'data/transactions_{i+1}.csv'
        with open(file_name, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['transaction_id', 'customer_id', 'product_id', 'quantity', 'transaction_date', 'branch'])
            for j in range(transactions_per_file):
                transaction_id = i * transactions_per_file + j + 1
                customer_id = random.randint(1, 2000)
                product_id = random.choice(product_ids)
                quantity = random.randint(1, 5)
                transaction_date = start_date + timedelta(seconds=random.randint(0, 3*24*60*60))
                branch = random.choice(branches)
                writer.writerow([transaction_id, customer_id, product_id, quantity, transaction_date.strftime('%Y-%m-%d %H:%M:%S'), branch])

def generate_customers(db_path='db/customers.db', num_customers=2000):
    """Generates customer data and stores it in a SQLite database."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute('DROP TABLE IF EXISTS customers')
    cursor.execute('''
    CREATE TABLE customers (
        id INTEGER PRIMARY KEY,
        first_name TEXT,
        last_name TEXT,
        address TEXT
    )
    ''')

    for i in range(1, num_customers + 1):
        cursor.execute("INSERT INTO customers (id, first_name, last_name, address) VALUES (?, ?, ?, ?)",
                       (i, fake.first_name(), fake.last_name(), fake.address().replace('\n', ', ')))

    conn.commit()
    conn.close()

def main():
    """Main function to generate all sample data."""
    # Create directories if they don't exist
    os.makedirs('data', exist_ok=True)
    os.makedirs('db', exist_ok=True)

    global fake
    fake = Faker()

    print("Generating products...")
    products = generate_products()
    with open('data/products.json', 'w') as f:
        json.dump(products, f, indent=4)
    print("Products generated successfully.")

    print("Generating transactions...")
    generate_transactions(products)
    print("Transactions generated successfully.")

    print("Generating customers...")
    generate_customers()
    print("Customers generated successfully.")

    print("\nSample data generation complete!")

if __name__ == "__main__":
    main()


