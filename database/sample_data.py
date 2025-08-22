import sqlite3
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.models import get_db_connection, generate_product_id, generate_user_id, hash_password
from database.operations import DatabaseOperations

def populate_sample_data():
    """Populate database with sample data for testing"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    print("Populating sample data...")
    
    # Add categories
    categories = [
        ("Fruits", "Fresh seasonal fruits", "https://images.unsplash.com/photo-1610832958506-aa56368176cf"),
        ("Vegetables", "Farm fresh vegetables", "https://images.unsplash.com/photo-1540420773420-3366772f4999"),
        ("Dairy & Eggs", "Fresh dairy products and eggs", "https://images.unsplash.com/photo-1563636619-e9143da7973b"),
        ("Snacks & Beverages", "Snacks and cold drinks", "https://images.unsplash.com/photo-1566478989037-eec170784d0b"),
        ("Packaged Foods", "Packaged and ready-to-eat foods", "https://images.unsplash.com/photo-1556909114-f6e7ad7d3136"),
        ("Personal Care", "Health and personal care products", "https://images.unsplash.com/photo-1556228578-dd6e4aaff14d")
    ]
    
    category_ids = {}
    for cat in categories:
        try:
            cursor.execute('''
                INSERT INTO categories (name, description, image_url)
                VALUES (?, ?, ?)
            ''', cat)
            category_id = cursor.lastrowid
            category_ids[cat[0]] = category_id
        except sqlite3.IntegrityError:
            # Category already exists, get its ID
            cursor.execute('SELECT id FROM categories WHERE name = ?', (cat[0],))
            category_ids[cat[0]] = cursor.fetchone()[0]
    
    # Add sample products
    products = [
        # Fruits
        ("Fresh Bananas", "Sweet and ripe bananas", "Fruits", 60, 80, "kg", 50, "https://images.unsplash.com/photo-1571771894821-ce9b6c11b08e"),
        ("Red Apples", "Crisp and juicy red apples", "Fruits", 120, 150, "kg", 30, "https://images.unsplash.com/photo-1560806887-1e4cd0b6cbd6"),
        ("Fresh Oranges", "Vitamin C rich oranges", "Fruits", 80, 100, "kg", 25, "https://images.unsplash.com/photo-1547036967-23d11aacaee0"),
        ("Mango (Seasonal)", "Sweet alphonso mangoes", "Fruits", 200, 250, "kg", 15, "https://images.unsplash.com/photo-1605027990121-cbae9c0a28d9"),
        
        # Vegetables
        ("Fresh Tomatoes", "Farm fresh red tomatoes", "Vegetables", 40, 50, "kg", 40, "https://images.unsplash.com/photo-1546470427-227e95ed9711"),
        ("Green Onions", "Fresh green onions", "Vegetables", 30, 40, "kg", 20, "https://images.unsplash.com/photo-1525082665-1c6d4d81e5b3"),
        ("Potatoes", "Fresh potatoes for cooking", "Vegetables", 25, 35, "kg", 60, "https://images.unsplash.com/photo-1518977676601-b53f82aba655"),
        ("Carrots", "Orange carrots rich in vitamin A", "Vegetables", 50, 60, "kg", 35, "https://images.unsplash.com/photo-1598170845058-32b9d6a5da37"),
        ("Spinach", "Fresh green spinach leaves", "Vegetables", 40, 50, "kg", 25, "https://images.unsplash.com/photo-1576045057995-568f588f82fb"),
        
        # Dairy & Eggs
        ("Fresh Milk", "Full cream fresh milk", "Dairy & Eggs", 60, 65, "liter", 50, "https://images.unsplash.com/photo-1563636619-e9143da7973b"),
        ("Farm Eggs", "Fresh farm eggs", "Dairy & Eggs", 120, 140, "dozen", 30, "https://images.unsplash.com/photo-1582722872445-44dc5f7e3c8f"),
        ("Greek Yogurt", "Thick and creamy yogurt", "Dairy & Eggs", 80, 90, "cup", 20, "https://images.unsplash.com/photo-1571212515416-0b8a1b7b5d6a"),
        ("Paneer", "Fresh cottage cheese", "Dairy & Eggs", 200, 220, "kg", 15, "https://images.unsplash.com/photo-1631452180539-96aca7d48617"),
        
        # Snacks & Beverages
        ("Coca Cola", "Refreshing cold drink", "Snacks & Beverages", 40, 45, "bottle", 100, "https://images.unsplash.com/photo-1629203851122-3726ecdf080e"),
        ("Potato Chips", "Crispy potato chips", "Snacks & Beverages", 30, 35, "packet", 80, "https://images.unsplash.com/photo-1566478989037-eec170784d0b"),
        ("Biscuits", "Sweet chocolate biscuits", "Snacks & Beverages", 25, 30, "packet", 60, "https://images.unsplash.com/photo-1558961363-fa8fdf82db35"),
        ("Fresh Juice", "Mixed fruit juice", "Snacks & Beverages", 60, 70, "bottle", 40, "https://images.unsplash.com/photo-1622597467836-f3285f2131b8"),
        
        # Packaged Foods
        ("Basmati Rice", "Premium basmati rice", "Packaged Foods", 150, 180, "kg", 100, "https://images.unsplash.com/photo-1586201375761-83865001e31c"),
        ("Wheat Flour", "Fresh ground wheat flour", "Packaged Foods", 45, 50, "kg", 80, "https://images.unsplash.com/photo-1574323347407-f5e1ad6d020b"),
        ("Cooking Oil", "Refined sunflower oil", "Packaged Foods", 120, 140, "liter", 50, "https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5"),
        ("Dal (Lentils)", "Mixed dal variety pack", "Packaged Foods", 90, 100, "kg", 70, "https://images.unsplash.com/photo-1596797038530-2c107229654b"),
        
        # Personal Care
        ("Hand Sanitizer", "Alcohol-based sanitizer", "Personal Care", 80, 90, "bottle", 40, "https://images.unsplash.com/photo-1584362917165-526a968579e8"),
        ("Face Mask", "Disposable face masks", "Personal Care", 100, 120, "packet", 30, "https://images.unsplash.com/photo-1584634731339-252c581abfc5"),
        ("Soap", "Antibacterial soap", "Personal Care", 40, 50, "piece", 60, "https://images.unsplash.com/photo-1520012449555-0db84ba2b9c7"),
        ("Shampoo", "Hair care shampoo", "Personal Care", 150, 180, "bottle", 25, "https://images.unsplash.com/photo-1556228578-dd6e4aaff14d")
    ]
    
    for product in products:
        product_id = generate_product_id()
        category_id = category_ids.get(product[2])
        
        cursor.execute('''
            INSERT INTO products (product_id, name, description, category_id, price, 
                                original_price, unit, stock_quantity, image_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (product_id, product[0], product[1], category_id, product[3], 
              product[4], product[5], product[6], product[7]))
    
    # Add sample users
    sample_users = [
        ("Prakhar Gupta", "9754373333", "prakhar@radheradheandsons.com", "admin123", True),  # Admin
        ("Rajesh Kumar", "9876543210", "rajesh@email.com", "password123", False),
        ("Priya Sharma", "9123456789", "priya@email.com", "password123", False),
        ("Anjali Gupta", "9234567890", "anjali@email.com", "password123", False),
        ("Demo User", "9999999999", "demo@email.com", "demo123", False)
    ]
    
    for user in sample_users:
        user_id = generate_user_id()
        password_hash = hash_password(user[3])
        
        try:
            cursor.execute('''
                INSERT INTO users (user_id, name, phone, email, password_hash, is_admin, loyalty_points)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, user[0], user[1], user[2], password_hash, user[4], 150))
        except sqlite3.IntegrityError:
            print(f"User {user[0]} already exists, skipping...")
    
    # Add sample addresses for demo user
    cursor.execute('SELECT user_id FROM users WHERE phone = "9999999999"')
    demo_user = cursor.fetchone()
    
    if demo_user:
        demo_user_id = demo_user[0]
        
        sample_addresses = [
            (demo_user_id, "Home", "123 Green Park, Sector 15", "Near City Mall", "110001", True),
            (demo_user_id, "Office", "456 Business Hub, Cyber City", "Tower B", "110002", False)
        ]
        
        for addr in sample_addresses:
            try:
                cursor.execute('''
                    INSERT INTO user_addresses (user_id, address_type, full_address, landmark, pincode, is_default)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', addr)
            except sqlite3.IntegrityError:
                pass
    
    # Add sample coupons
    sample_coupons = [
        ("WELCOME10", "Welcome offer - 10% off", "percentage", 10, 200, 100),
        ("FLAT50", "Flat ₹50 off", "flat", 50, 300, 50),
        ("FIRST20", "First time user - 20% off", "percentage", 20, 150, 200)
    ]
    
    for coupon in sample_coupons:
        try:
            cursor.execute('''
                INSERT INTO coupons (code, description, discount_type, discount_value, min_order_value, max_discount)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', coupon)
        except sqlite3.IntegrityError:
            pass
    
    conn.commit()
    conn.close()
    
    print("Sample data populated successfully!")
    print("\nDemo Login Credentials:")
    print("Admin - Phone: 9754373333, Password: admin123")
    print("User - Phone: 9999999999, Password: demo123")

if __name__ == "__main__":
    from database.models import init_database
    init_database()
    populate_sample_data()
