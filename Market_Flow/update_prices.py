import json
import sqlite3
import random

def update_product_price():
    """Updates the price of a random product in the products.json file."""
    with open('data/products.json', 'r+') as f:
        products = json.load(f)
        
        # Select a random product to update
        product_to_update = random.choice(products)
        old_price = product_to_update['price']
        new_price = round(old_price * random.uniform(1.1, 1.5), 2)
        product_to_update['price'] = new_price
        
        # Go back to the beginning of the file to overwrite
        f.seek(0)
        json.dump(products, f, indent=4)
        f.truncate()
        
        print(f"Updated product ID {product_to_update['id']}: price changed from {old_price} to {new_price}")
        return product_to_update['id'], new_price

def update_orders_table(product_id, new_price):
    """Updates the amount in the orders table for a given product."""
    try:
        conn = sqlite3.connect('db/orders.db')
        cursor = conn.cursor()

        cursor.execute("""
        UPDATE orders
        SET amount = quantity * ?
        WHERE product_id = ?
        """, (new_price, product_id))

        conn.commit()
        print(f"Successfully updated {cursor.rowcount} orders for product ID {product_id}.")

    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if 'conn' in locals() and conn:
            conn.close()

def main():
    """Main function to update product prices and reflect changes in the orders table."""
    product_id, new_price = update_product_price()
    update_orders_table(product_id, new_price)

if __name__ == "__main__":
    main()
