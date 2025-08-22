import sqlite3
from datetime import datetime, timedelta
import random
from .models import (
    get_db_connection, hash_password, verify_password, 
    generate_user_id, generate_order_id, generate_product_id
)

class DatabaseOperations:
    
    # User Operations
    @staticmethod
    def create_user(name, phone, email=None, password=None):
        """Create a new user"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        user_id = generate_user_id()
        password_hash = hash_password(password) if password else hash_password("123456")  # Default password
        
        try:
            cursor.execute('''
                INSERT INTO users (user_id, name, email, phone, password_hash)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, name, email, phone, password_hash))
            conn.commit()
            return user_id
        except sqlite3.IntegrityError:
            return None
        finally:
            conn.close()
    
    @staticmethod
    def authenticate_user(phone, password):
        """Authenticate user with phone and password"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT user_id, name, email, is_admin, password_hash
            FROM users WHERE phone = ?
        ''', (phone,))
        
        user = cursor.fetchone()
        conn.close()
        
        if user and verify_password(password, user[4]):
            return {
                'user_id': user[0],
                'name': user[1],
                'email': user[2],
                'is_admin': user[3]
            }
        return None
    
    @staticmethod
    def get_user_by_id(user_id):
        """Get user details by user_id"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT user_id, name, email, phone, loyalty_points, is_admin
            FROM users WHERE user_id = ?
        ''', (user_id,))
        
        user = cursor.fetchone()
        conn.close()
        
        if user:
            return {
                'user_id': user[0],
                'name': user[1],
                'email': user[2],
                'phone': user[3],
                'loyalty_points': user[4],
                'is_admin': user[5]
            }
        return None
    
    # OTP Operations
    @staticmethod
    def generate_otp(phone):
        """Generate and store OTP for phone number"""
        otp = str(random.randint(100000, 999999))
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Delete existing OTP for this phone
        cursor.execute('DELETE FROM otp_verification WHERE phone = ?', (phone,))
        
        # Insert new OTP
        cursor.execute('''
            INSERT INTO otp_verification (phone, otp)
            VALUES (?, ?)
        ''', (phone, otp))
        
        conn.commit()
        conn.close()
        return otp
    
    @staticmethod
    def verify_otp(phone, otp):
        """Verify OTP for phone number"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id FROM otp_verification 
            WHERE phone = ? AND otp = ? AND is_verified = FALSE
            AND datetime(created_at, '+10 minutes') > datetime('now')
        ''', (phone, otp))
        
        result = cursor.fetchone()
        
        if result:
            # Mark OTP as verified
            cursor.execute('''
                UPDATE otp_verification SET is_verified = TRUE WHERE id = ?
            ''', (result[0],))
            conn.commit()
            conn.close()
            return True
        
        conn.close()
        return False
    
    # Category Operations
    @staticmethod
    def get_categories():
        """Get all active categories"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, name, description, image_url
            FROM categories WHERE is_active = TRUE
        ''')
        
        categories = cursor.fetchall()
        conn.close()
        
        return [
            {'id': cat[0], 'name': cat[1], 'description': cat[2], 'image_url': cat[3]}
            for cat in categories
        ]
    
    # Product Operations
    @staticmethod
    def get_products(category_id=None, search_query=None, limit=50):
        """Get products with optional filters"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        base_query = '''
            SELECT p.product_id, p.name, p.description, p.price, p.original_price,
                   p.unit, p.stock_quantity, p.image_url, c.name as category_name
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE p.is_active = TRUE
        '''
        
        params = []
        
        if category_id:
            base_query += " AND p.category_id = ?"
            params.append(category_id)
        
        if search_query:
            base_query += " AND (p.name LIKE ? OR p.description LIKE ?)"
            search_term = f"%{search_query}%"
            params.extend([search_term, search_term])
        
        base_query += f" LIMIT {limit}"
        
        cursor.execute(base_query, params)
        products = cursor.fetchall()
        conn.close()
        
        return [
            {
                'product_id': p[0], 'name': p[1], 'description': p[2],
                'price': p[3], 'original_price': p[4], 'unit': p[5],
                'stock_quantity': p[6], 'image_url': p[7], 'category_name': p[8]
            }
            for p in products
        ]
    
    @staticmethod
    def get_product_by_id(product_id):
        """Get single product details"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT p.product_id, p.name, p.description, p.price, p.original_price,
                   p.unit, p.stock_quantity, p.image_url, c.name as category_name
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE p.product_id = ? AND p.is_active = TRUE
        ''', (product_id,))
        
        product = cursor.fetchone()
        conn.close()
        
        if product:
            return {
                'product_id': product[0], 'name': product[1], 'description': product[2],
                'price': product[3], 'original_price': product[4], 'unit': product[5],
                'stock_quantity': product[6], 'image_url': product[7], 'category_name': product[8]
            }
        return None
    
    # Cart Operations
    @staticmethod
    def add_to_cart(user_id, product_id, quantity=1):
        """Add product to cart"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO cart (user_id, product_id, quantity, added_at)
                VALUES (?, ?, 
                    CASE 
                        WHEN EXISTS(SELECT 1 FROM cart WHERE user_id=? AND product_id=?) 
                        THEN (SELECT quantity FROM cart WHERE user_id=? AND product_id=?) + ?
                        ELSE ?
                    END,
                    CURRENT_TIMESTAMP)
            ''', (user_id, product_id, user_id, product_id, user_id, product_id, quantity, quantity))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error adding to cart: {e}")
            return False
        finally:
            conn.close()
    
    @staticmethod
    def get_cart_items(user_id):
        """Get cart items for user"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT c.product_id, c.quantity, p.name, p.price, p.unit, p.image_url,
                   (c.quantity * p.price) as total_price
            FROM cart c
            JOIN products p ON c.product_id = p.product_id
            WHERE c.user_id = ? AND p.is_active = TRUE
        ''', (user_id,))
        
        items = cursor.fetchall()
        conn.close()
        
        return [
            {
                'product_id': item[0], 'quantity': item[1], 'name': item[2],
                'price': item[3], 'unit': item[4], 'image_url': item[5],
                'total_price': item[6]
            }
            for item in items
        ]
    
    @staticmethod
    def update_cart_quantity(user_id, product_id, quantity):
        """Update cart item quantity"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if quantity <= 0:
            cursor.execute('''
                DELETE FROM cart WHERE user_id = ? AND product_id = ?
            ''', (user_id, product_id))
        else:
            cursor.execute('''
                UPDATE cart SET quantity = ? WHERE user_id = ? AND product_id = ?
            ''', (quantity, user_id, product_id))
        
        conn.commit()
        conn.close()
    
    @staticmethod
    def clear_cart(user_id):
        """Clear user cart"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM cart WHERE user_id = ?', (user_id,))
        conn.commit()
        conn.close()
    
    # Order Operations
    @staticmethod
    def create_order(user_id, delivery_address, phone, payment_method, cart_items, 
                    total_amount, delivery_charges=30, discount_amount=0, coupon_code=None):
        """Create new order"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        order_id = generate_order_id()
        estimated_delivery = datetime.now() + timedelta(hours=2)
        
        try:
            # Create order
            cursor.execute('''
                INSERT INTO orders (order_id, user_id, total_amount, delivery_address,
                                  phone, payment_method, delivery_charges, discount_amount,
                                  coupon_code, estimated_delivery)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (order_id, user_id, total_amount, delivery_address, phone, payment_method,
                  delivery_charges, discount_amount, coupon_code, estimated_delivery))
            
            # Add order items
            for item in cart_items:
                cursor.execute('''
                    INSERT INTO order_items (order_id, product_id, quantity, price)
                    VALUES (?, ?, ?, ?)
                ''', (order_id, item['product_id'], item['quantity'], item['price']))
            
            # Clear cart
            cursor.execute('DELETE FROM cart WHERE user_id = ?', (user_id,))
            
            conn.commit()
            return order_id
        except Exception as e:
            print(f"Error creating order: {e}")
            conn.rollback()
            return None
        finally:
            conn.close()
    
    @staticmethod
    def get_user_orders(user_id):
        """Get user order history"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT order_id, total_amount, order_status, payment_status,
                   created_at, estimated_delivery
            FROM orders
            WHERE user_id = ?
            ORDER BY created_at DESC
        ''', (user_id,))
        
        orders = cursor.fetchall()
        conn.close()
        
        return [
            {
                'order_id': order[0], 'total_amount': order[1],
                'order_status': order[2], 'payment_status': order[3],
                'created_at': order[4], 'estimated_delivery': order[5]
            }
            for order in orders
        ]
    
    @staticmethod
    def get_order_details(order_id):
        """Get detailed order information"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get order info
        cursor.execute('''
            SELECT o.order_id, o.total_amount, o.delivery_address, o.phone,
                   o.payment_method, o.order_status, o.payment_status,
                   o.delivery_charges, o.discount_amount, o.created_at,
                   o.estimated_delivery, u.name
            FROM orders o
            JOIN users u ON o.user_id = u.user_id
            WHERE o.order_id = ?
        ''', (order_id,))
        
        order = cursor.fetchone()
        
        if not order:
            conn.close()
            return None
        
        # Get order items
        cursor.execute('''
            SELECT oi.product_id, oi.quantity, oi.price, p.name, p.unit
            FROM order_items oi
            JOIN products p ON oi.product_id = p.product_id
            WHERE oi.order_id = ?
        ''', (order_id,))
        
        items = cursor.fetchall()
        conn.close()
        
        return {
            'order_id': order[0], 'total_amount': order[1], 'delivery_address': order[2],
            'phone': order[3], 'payment_method': order[4], 'order_status': order[5],
            'payment_status': order[6], 'delivery_charges': order[7], 'discount_amount': order[8],
            'created_at': order[9], 'estimated_delivery': order[10], 'customer_name': order[11],
            'items': [
                {
                    'product_id': item[0], 'quantity': item[1], 'price': item[2],
                    'name': item[3], 'unit': item[4]
                }
                for item in items
            ]
        }
    
    # Address Operations
    @staticmethod
    def add_user_address(user_id, address_type, full_address, landmark, pincode, is_default=False):
        """Add user address"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # If this is default, update others
        if is_default:
            cursor.execute('''
                UPDATE user_addresses SET is_default = FALSE WHERE user_id = ?
            ''', (user_id,))
        
        cursor.execute('''
            INSERT INTO user_addresses (user_id, address_type, full_address, landmark, pincode, is_default)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, address_type, full_address, landmark, pincode, is_default))
        
        conn.commit()
        conn.close()
    
    @staticmethod
    def get_user_addresses(user_id):
        """Get user addresses"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, address_type, full_address, landmark, pincode, is_default
            FROM user_addresses WHERE user_id = ?
            ORDER BY is_default DESC, address_type
        ''', (user_id,))
        
        addresses = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': addr[0], 'address_type': addr[1], 'full_address': addr[2],
                'landmark': addr[3], 'pincode': addr[4], 'is_default': addr[5]
            }
            for addr in addresses
        ]
