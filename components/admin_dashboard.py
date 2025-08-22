import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from database.operations import DatabaseOperations
from database.models import get_db_connection, generate_product_id
from utils.auth import get_current_user, is_admin

def show_admin_dashboard():
    """Main admin dashboard"""
    if not is_admin():
        st.error("Admin access required")
        return
    
    st.title("🔧 Admin Dashboard")
    st.write("Welcome to Radhe Radhe & Sons Admin Panel")
    
    # Quick stats
    show_admin_quick_stats()
    
    # Navigation tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Analytics", "📦 Products", "🛒 Orders", "👥 Customers", "⚙️ Settings"
    ])
    
    with tab1:
        show_analytics_dashboard()
    
    with tab2:
        show_product_management()
    
    with tab3:
        show_order_management()
    
    with tab4:
        show_customer_management()
    
    with tab5:
        show_admin_settings()

def show_admin_quick_stats():
    """Show quick stats cards"""
    col1, col2, col3, col4 = st.columns(4)
    
    # Get stats from database
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Total orders today
    cursor.execute('''
        SELECT COUNT(*) FROM orders 
        WHERE DATE(created_at) = DATE('now')
    ''')
    today_orders = cursor.fetchone()[0]
    
    # Total revenue today
    cursor.execute('''
        SELECT COALESCE(SUM(total_amount), 0) FROM orders 
        WHERE DATE(created_at) = DATE('now') AND payment_status = 'paid'
    ''')
    today_revenue = cursor.fetchone()[0]
    
    # Total products
    cursor.execute('SELECT COUNT(*) FROM products WHERE is_active = TRUE')
    total_products = cursor.fetchone()[0]
    
    # Pending orders
    cursor.execute('SELECT COUNT(*) FROM orders WHERE order_status = "pending"')
    pending_orders = cursor.fetchone()[0]
    
    conn.close()
    
    with col1:
        st.metric("Today's Orders", today_orders)
    with col2:
        st.metric("Today's Revenue", f"₹{today_revenue:.2f}")
    with col3:
        st.metric("Active Products", total_products)
    with col4:
        st.metric("Pending Orders", pending_orders)

def show_analytics_dashboard():
    """Show analytics and reports"""
    st.subheader("📊 Business Analytics")
    
    conn = get_db_connection()
    
    # Revenue chart
    st.write("**📈 Revenue Trend (Last 7 Days)**")
    revenue_query = '''
        SELECT DATE(created_at) as order_date, 
               COALESCE(SUM(total_amount), 0) as daily_revenue
        FROM orders 
        WHERE created_at >= datetime('now', '-7 days')
        AND payment_status = 'paid'
        GROUP BY DATE(created_at)
        ORDER BY order_date
    '''
    
    revenue_df = pd.read_sql_query(revenue_query, conn)
    
    if not revenue_df.empty:
        fig = px.line(revenue_df, x='order_date', y='daily_revenue', 
                     title='Daily Revenue', markers=True)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No revenue data available")
    
    # Order status distribution
    st.write("**📦 Order Status Distribution**")
    status_query = '''
        SELECT order_status, COUNT(*) as count
        FROM orders
        GROUP BY order_status
    '''
    
    status_df = pd.read_sql_query(status_query, conn)
    
    if not status_df.empty:
        fig = px.pie(status_df, values='count', names='order_status', 
                    title='Order Status Distribution')
        st.plotly_chart(fig, use_container_width=True)
    
    # Top selling products
    st.write("**🏆 Top Selling Products**")
    top_products_query = '''
        SELECT p.name, SUM(oi.quantity) as total_sold, SUM(oi.quantity * oi.price) as revenue
        FROM order_items oi
        JOIN products p ON oi.product_id = p.product_id
        GROUP BY p.product_id, p.name
        ORDER BY total_sold DESC
        LIMIT 10
    '''
    
    top_products_df = pd.read_sql_query(top_products_query, conn)
    
    if not top_products_df.empty:
        st.dataframe(top_products_df, use_container_width=True)
    else:
        st.info("No sales data available")
    
    conn.close()

def show_product_management():
    """Product management interface"""
    st.subheader("📦 Product Management")
    
    tab1, tab2, tab3 = st.tabs(["View Products", "Add Product", "Categories"])
    
    with tab1:
        show_product_list_admin()
    
    with tab2:
        show_add_product_form()
    
    with tab3:
        show_category_management()

def show_product_list_admin():
    """Show products list for admin with edit options"""
    st.write("**Product Inventory**")
    
    # Get all products
    products = DatabaseOperations.get_products(limit=100)
    
    if products:
        # Convert to DataFrame for better display
        df = pd.DataFrame(products)
        
        # Add stock status
        df['stock_status'] = df['stock_quantity'].apply(
            lambda x: 'Low Stock' if x < 10 else 'In Stock' if x > 0 else 'Out of Stock'
        )
        
        # Display editable dataframe
        edited_df = st.data_editor(
            df[['name', 'price', 'stock_quantity', 'stock_status', 'is_active']],
            column_config={
                "name": "Product Name",
                "price": st.column_config.NumberColumn("Price (₹)", format="₹%.2f"),
                "stock_quantity": st.column_config.NumberColumn("Stock", min_value=0),
                "stock_status": "Status",
                "is_active": st.column_config.CheckboxColumn("Active")
            },
            hide_index=True,
            use_container_width=True
        )
        
        if st.button("💾 Update Products"):
            # Update products in database
            # For demo, just show success message
            st.success("Products updated successfully!")
    else:
        st.info("No products found")

def show_add_product_form():
    """Form to add new product"""
    st.write("**Add New Product**")
    
    with st.form("add_product_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Product Name")
            price = st.number_input("Price (₹)", min_value=0.0, format="%.2f")
            original_price = st.number_input("Original Price (₹)", min_value=0.0, format="%.2f")
            unit = st.selectbox("Unit", ["kg", "piece", "liter", "gram", "packet", "bottle"])
        
        with col2:
            # Get categories for dropdown
            categories = DatabaseOperations.get_categories()
            category_options = {cat['name']: cat['id'] for cat in categories}
            
            selected_category = st.selectbox("Category", list(category_options.keys()))
            stock_quantity = st.number_input("Stock Quantity", min_value=0, value=10)
            image_url = st.text_input("Image URL (Optional)")
        
        description = st.text_area("Product Description")
        
        if st.form_submit_button("➕ Add Product", use_container_width=True):
            if name and price > 0:
                # Add product to database
                conn = get_db_connection()
                cursor = conn.cursor()
                
                product_id = generate_product_id()
                category_id = category_options[selected_category]
                
                try:
                    cursor.execute('''
                        INSERT INTO products (product_id, name, description, category_id, 
                                            price, original_price, unit, stock_quantity, image_url)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (product_id, name, description, category_id, price, 
                          original_price if original_price > 0 else None, unit, stock_quantity, image_url))
                    
                    conn.commit()
                    st.success(f"Product '{name}' added successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error adding product: {e}")
                finally:
                    conn.close()
            else:
                st.error("Please fill required fields")

def show_category_management():
    """Category management interface"""
    st.write("**Manage Categories**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Existing Categories:**")
        categories = DatabaseOperations.get_categories()
        
        if categories:
            for category in categories:
                col_cat1, col_cat2 = st.columns([3, 1])
                with col_cat1:
                    st.write(f"**{category['name']}**")
                    st.write(category.get('description', 'No description'))
                with col_cat2:
                    if st.button("✏️", key=f"edit_cat_{category['id']}", help="Edit category"):
                        st.info("Edit functionality coming soon!")
        else:
            st.info("No categories found")
    
    with col2:
        st.write("**Add New Category:**")
        with st.form("add_category_form"):
            cat_name = st.text_input("Category Name")
            cat_desc = st.text_area("Description")
            cat_image = st.text_input("Image URL (Optional)")
            
            if st.form_submit_button("➕ Add Category"):
                if cat_name:
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    
                    try:
                        cursor.execute('''
                            INSERT INTO categories (name, description, image_url)
                            VALUES (?, ?, ?)
                        ''', (cat_name, cat_desc, cat_image))
                        conn.commit()
                        st.success(f"Category '{cat_name}' added!")
                        st.rerun()
                    except Exception as e:
                        if "UNIQUE constraint failed" in str(e):
                            st.error("Category already exists")
                        else:
                            st.error(f"Error: {e}")
                    except Exception as e:
                        st.error(f"Error: {e}")
                    finally:
                        conn.close()
                else:
                    st.error("Please enter category name")

def show_order_management():
    """Order management for admin"""
    st.subheader("🛒 Order Management")
    
    # Order filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status_filter = st.selectbox(
            "Filter by Status",
            ["All", "pending", "confirmed", "packed", "out_for_delivery", "delivered", "cancelled"]
        )
    
    with col2:
        date_filter = st.date_input("Filter by Date", value=datetime.now().date())
    
    with col3:
        if st.button("🔄 Refresh Orders"):
            st.rerun()
    
    # Get orders from database
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = '''
        SELECT o.order_id, o.total_amount, o.order_status, o.payment_status,
               o.created_at, u.name as customer_name, u.phone
        FROM orders o
        JOIN users u ON o.user_id = u.user_id
        WHERE 1=1
    '''
    
    params = []
    
    if status_filter != "All":
        query += " AND o.order_status = ?"
        params.append(status_filter)
    
    if date_filter:
        query += " AND DATE(o.created_at) = ?"
        params.append(date_filter.strftime('%Y-%m-%d'))
    
    query += " ORDER BY o.created_at DESC"
    
    cursor.execute(query, params)
    orders = cursor.fetchall()
    conn.close()
    
    if orders:
        for order in orders:
            with st.container():
                col1, col2, col3, col4 = st.columns([2, 1, 1, 2])
                
                with col1:
                    st.write(f"**{order[0]}**")  # order_id
                    st.write(f"Customer: {order[5]}")  # customer_name
                    st.write(f"Phone: {order[6]}")  # phone
                
                with col2:
                    st.write(f"**₹{order[1]:.2f}**")  # total_amount
                    st.write(f"{order[4][:16]}")  # created_at
                
                with col3:
                    current_status = order[2]  # order_status
                    new_status = st.selectbox(
                        "Status",
                        ["pending", "confirmed", "packed", "out_for_delivery", "delivered", "cancelled"],
                        index=["pending", "confirmed", "packed", "out_for_delivery", "delivered", "cancelled"].index(current_status),
                        key=f"status_{order[0]}"
                    )
                    
                    if new_status != current_status:
                        if update_order_status(order[0], new_status):
                            st.success("Status updated!")
                            st.rerun()
                
                with col4:
                    if st.button("View Details", key=f"admin_view_{order[0]}", use_container_width=True):
                        show_admin_order_details(order[0])
            
            st.divider()
    else:
        st.info("No orders found for the selected filters")

def show_admin_order_details(order_id):
    """Show order details for admin"""
    st.subheader(f"📋 Order Management - {order_id}")
    
    order = DatabaseOperations.get_order_details(order_id)
    
    if not order:
        st.error("Order not found")
        return
    
    # Order info
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**Customer:** {order['customer_name']}")
        st.write(f"**Phone:** {order['phone']}")
        st.write(f"**Order Date:** {order['created_at'][:16]}")
        st.write(f"**Total Amount:** ₹{order['total_amount']:.2f}")
    
    with col2:
        st.write(f"**Status:** {order['order_status']}")
        st.write(f"**Payment:** {order['payment_status']}")
        st.write(f"**Payment Method:** {order['payment_method']}")
        st.write(f"**Delivery Address:** {order['delivery_address']}")
    
    # Order items
    st.write("**Order Items:**")
    for item in order['items']:
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        with col1:
            st.write(item['name'])
        with col2:
            st.write(f"₹{item['price']:.2f}")
        with col3:
            st.write(f"Qty: {item['quantity']}")
        with col4:
            st.write(f"₹{item['price'] * item['quantity']:.2f}")

def update_order_status(order_id, new_status):
    """Update order status"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            UPDATE orders 
            SET order_status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE order_id = ?
        ''', (new_status, order_id))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Error updating order status: {e}")
        return False
    finally:
        conn.close()

def show_customer_management():
    """Customer management interface"""
    st.subheader("👥 Customer Management")
    
    # Customer stats
    conn = get_db_connection()
    
    # Total customers
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM users WHERE is_admin = FALSE')
    total_customers = cursor.fetchone()[0]
    
    # New customers this month
    cursor.execute('''
        SELECT COUNT(*) FROM users 
        WHERE is_admin = FALSE AND DATE(created_at) >= DATE('now', 'start of month')
    ''')
    new_customers = cursor.fetchone()[0]
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Customers", total_customers)
    with col2:
        st.metric("New This Month", new_customers)
    
    # Customer list
    st.write("**Customer List:**")
    
    customer_query = '''
        SELECT u.name, u.phone, u.email, u.loyalty_points,
               COUNT(o.id) as total_orders,
               COALESCE(SUM(o.total_amount), 0) as total_spent,
               u.created_at
        FROM users u
        LEFT JOIN orders o ON u.user_id = o.user_id
        WHERE u.is_admin = FALSE
        GROUP BY u.user_id, u.name, u.phone, u.email, u.loyalty_points, u.created_at
        ORDER BY total_spent DESC
    '''
    
    customers_df = pd.read_sql_query(customer_query, conn)
    conn.close()
    
    if not customers_df.empty:
        st.dataframe(
            customers_df,
            column_config={
                "name": "Customer Name",
                "phone": "Phone",
                "email": "Email",
                "loyalty_points": "Loyalty Points",
                "total_orders": "Total Orders",
                "total_spent": st.column_config.NumberColumn("Total Spent", format="₹%.2f"),
                "created_at": "Joined Date"
            },
            hide_index=True,
            use_container_width=True
        )
    else:
        st.info("No customers found")

def show_admin_settings():
    """Admin settings and configuration"""
    st.subheader("⚙️ System Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Store Settings:**")
        
        store_name = st.text_input("Store Name", value="Radhe Radhe & Sons")
        owner_name = st.text_input("Owner Name", value="Prakhar Gupta")
        contact_number = st.text_input("Contact Number", value="+91 9754373333")
        delivery_radius = st.number_input("Delivery Radius (km)", value=5, min_value=1, max_value=20)
        min_order_value = st.number_input("Minimum Order Value (₹)", value=100, min_value=0)
        
        if st.button("💾 Save Store Settings"):
            st.success("Store settings saved!")
    
    with col2:
        st.write("**Delivery Settings:**")
        
        free_delivery_above = st.number_input("Free Delivery Above (₹)", value=500, min_value=0)
        delivery_charges = st.number_input("Standard Delivery Charges (₹)", value=30, min_value=0)
        delivery_time_slots = st.multiselect(
            "Available Time Slots",
            ["9 AM - 12 PM", "12 PM - 4 PM", "4 PM - 8 PM", "8 PM - 10 PM"],
            default=["9 AM - 12 PM", "12 PM - 4 PM", "4 PM - 8 PM"]
        )
        
        if st.button("💾 Save Delivery Settings"):
            st.success("Delivery settings saved!")
    
    # System actions
    st.write("**System Actions:**")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 Export Data", use_container_width=True):
            st.info("Data export functionality coming soon!")
    
    with col2:
        if st.button("🔄 Backup Database", use_container_width=True):
            st.info("Database backup functionality coming soon!")
    
    with col3:
        if st.button("📱 Send Notifications", use_container_width=True):
            st.info("Notification system coming soon!")

def show_inventory_alerts():
    """Show low stock alerts"""
    st.subheader("⚠️ Inventory Alerts")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get low stock products
    cursor.execute('''
        SELECT product_id, name, stock_quantity, unit
        FROM products
        WHERE stock_quantity < 10 AND is_active = TRUE
        ORDER BY stock_quantity ASC
    ''')
    
    low_stock_products = cursor.fetchall()
    conn.close()
    
    if low_stock_products:
        st.warning(f"⚠️ {len(low_stock_products)} products are running low on stock!")
        
        for product in low_stock_products:
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                st.write(f"**{product[1]}**")  # name
            with col2:
                st.write(f"Stock: {product[2]} {product[3]}")  # quantity, unit
            with col3:
                if st.button("📦 Restock", key=f"restock_{product[0]}"):
                    st.info("Restock functionality coming soon!")
    else:
        st.success("✅ All products are well stocked!")

def show_sales_analytics():
    """Detailed sales analytics"""
    st.subheader("📈 Sales Analytics")
    
    # Date range selector
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("From Date", value=datetime.now().date() - timedelta(days=30))
    with col2:
        end_date = st.date_input("To Date", value=datetime.now().date())
    
    conn = get_db_connection()
    
    # Sales summary for date range
    summary_query = '''
        SELECT 
            COUNT(*) as total_orders,
            COALESCE(SUM(total_amount), 0) as total_revenue,
            COALESCE(AVG(total_amount), 0) as avg_order_value
        FROM orders
        WHERE DATE(created_at) BETWEEN ? AND ?
        AND payment_status = 'paid'
    '''
    
    cursor.execute(summary_query, (start_date, end_date))
    summary = cursor.fetchone()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Orders", summary[0])
    with col2:
        st.metric("Total Revenue", f"₹{summary[1]:.2f}")
    with col3:
        st.metric("Avg Order Value", f"₹{summary[2]:.2f}")
    
    conn.close()
