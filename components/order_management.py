import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from database.operations import DatabaseOperations
from utils.auth import get_current_user

ORDER_STATUS_COLORS = {
    'pending': '🟡',
    'confirmed': '🔵', 
    'packed': '🟠',
    'out_for_delivery': '🚚',
    'delivered': '✅',
    'cancelled': '❌'
}

ORDER_STATUS_DESCRIPTIONS = {
    'pending': 'Order received and being processed',
    'confirmed': 'Order confirmed by store',
    'packed': 'Items packed and ready for pickup',
    'out_for_delivery': 'Order is on the way to you',
    'delivered': 'Order successfully delivered',
    'cancelled': 'Order has been cancelled'
}

def show_orders_page():
    """Display user orders page"""
    st.title("📦 My Orders")
    
    user = get_current_user()
    if not user:
        st.warning("Please login to view your orders")
        return
    
    # Check if showing order confirmation
    if 'order_placed' in st.session_state:
        from components.cart_checkout import show_order_confirmation
        show_order_confirmation(st.session_state.order_placed)
        del st.session_state.order_placed
        return
    
    orders = DatabaseOperations.get_user_orders(user['user_id'])
    
    if not orders:
        st.info("You haven't placed any orders yet.")
        if st.button("🛍️ Start Shopping", use_container_width=True):
            st.session_state.current_page = 'products'
            st.rerun()
        return
    
    # Order filter
    col1, col2 = st.columns([1, 3])
    with col1:
        status_filter = st.selectbox(
            "Filter by status",
            ["All Orders", "pending", "confirmed", "packed", "out_for_delivery", "delivered", "cancelled"]
        )
    
    # Filter orders if needed
    if status_filter != "All Orders":
        filtered_orders = [order for order in orders if order['order_status'] == status_filter]
    else:
        filtered_orders = orders
    
    # Display orders
    for order in filtered_orders:
        with st.container():
            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
            
            with col1:
                st.write(f"**Order #{order['order_id']}**")
                st.write(f"Placed on: {order['created_at'][:10]}")
            
            with col2:
                status_emoji = ORDER_STATUS_COLORS.get(order['order_status'], '⚪')
                st.write(f"**Status:** {status_emoji} {order['order_status'].title()}")
            
            with col3:
                st.write(f"**Total:** ₹{order['total_amount']:.2f}")
                payment_color = "🟢" if order['payment_status'] == 'paid' else "🟡"
                st.write(f"**Payment:** {payment_color} {order['payment_status'].title()}")
            
            with col4:
                if st.button("View Details", key=f"view_{order['order_id']}", use_container_width=True):
                    show_order_details(order['order_id'])
                
                if order['order_status'] in ['pending', 'confirmed'] and st.button(
                    "Cancel", key=f"cancel_{order['order_id']}", use_container_width=True
                ):
                    if cancel_order(order['order_id']):
                        st.success("Order cancelled successfully")
                        st.rerun()
        
        st.divider()

def show_order_details(order_id):
    """Show detailed view of a specific order"""
    st.subheader(f"📋 Order Details - {order_id}")
    
    order = DatabaseOperations.get_order_details(order_id)
    
    if not order:
        st.error("Order not found")
        return
    
    # Order information
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**Customer:** {order['customer_name']}")
        st.write(f"**Order Date:** {order['created_at'][:16]}")
        st.write(f"**Phone:** {order['phone']}")
        st.write(f"**Payment Method:** {order['payment_method']}")
    
    with col2:
        status_emoji = ORDER_STATUS_COLORS.get(order['order_status'], '⚪')
        st.write(f"**Status:** {status_emoji} {order['order_status'].title()}")
        st.write(f"**Payment Status:** {order['payment_status'].title()}")
        st.write(f"**Estimated Delivery:** {order['estimated_delivery'][:16]}")
    
    # Delivery address
    st.write(f"**Delivery Address:** {order['delivery_address']}")
    
    # Order tracking
    show_order_tracking(order['order_status'])
    
    # Order items
    st.subheader("📦 Order Items")
    
    total_items = 0
    for item in order['items']:
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        
        with col1:
            st.write(f"**{item['name']}**")
        with col2:
            st.write(f"₹{item['price']:.2f}/{item['unit']}")
        with col3:
            st.write(f"Qty: {item['quantity']}")
        with col4:
            st.write(f"₹{item['price'] * item['quantity']:.2f}")
        
        total_items += item['quantity']
    
    # Order summary
    st.subheader("💰 Order Summary")
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**Items ({total_items}):** ₹{order['total_amount'] - order['delivery_charges'] + order['discount_amount']:.2f}")
        if order['discount_amount'] > 0:
            st.write(f"**Discount:** -₹{order['discount_amount']:.2f}")
        st.write(f"**Delivery Charges:** ₹{order['delivery_charges']:.2f}")
    
    with col2:
        st.write(f"**Total Amount:** ₹{order['total_amount']:.2f}")
    
    # Action buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Reorder", use_container_width=True):
            reorder_items(order['items'])
    
    with col2:
        if order['order_status'] in ['delivered'] and st.button("⭐ Rate Order", use_container_width=True):
            show_rating_form(order_id)
    
    with col3:
        if st.button("📞 Support", use_container_width=True):
            st.info("📞 Call: +91 9754373333\n📧 Email: support@radheradheandsons.com")

def show_order_tracking(current_status):
    """Show order tracking timeline"""
    st.subheader("🚚 Order Tracking")
    
    statuses = ['pending', 'confirmed', 'packed', 'out_for_delivery', 'delivered']
    status_names = ['Order Placed', 'Confirmed', 'Packed', 'Out for Delivery', 'Delivered']
    
    current_index = statuses.index(current_status) if current_status in statuses else 0
    
    # Create tracking timeline
    cols = st.columns(len(statuses))
    
    for i, (status, name) in enumerate(zip(statuses, status_names)):
        with cols[i]:
            if i <= current_index:
                st.markdown(f"**✅ {name}**")
                st.write(ORDER_STATUS_DESCRIPTIONS.get(status, ''))
            else:
                st.markdown(f"⚪ {name}")
                st.write("Pending")
    
    # Progress bar
    progress = (current_index + 1) / len(statuses)
    st.progress(progress)
    
    # Estimated delivery time
    if current_status == 'out_for_delivery':
        st.info("🚚 Your order will be delivered within 30-60 minutes")
    elif current_status in ['pending', 'confirmed', 'packed']:
        estimated_time = 90 - (current_index * 20)
        st.info(f"⏰ Estimated delivery in {estimated_time}-120 minutes")

def reorder_items(order_items):
    """Add order items back to cart for reorder"""
    user = get_current_user()
    if not user:
        st.warning("Please login to reorder")
        return
    
    added_count = 0
    for item in order_items:
        if DatabaseOperations.add_to_cart(user['user_id'], item['product_id'], item['quantity']):
            added_count += 1
    
    if added_count > 0:
        st.success(f"Added {added_count} items to cart!")
        from utils.auth import update_cart_count
        update_cart_count()
        st.session_state.current_page = 'cart'
        st.rerun()
    else:
        st.error("Failed to add items to cart")

def cancel_order(order_id):
    """Cancel an order"""
    # In a real app, this would update the order status in database
    # For demo, we'll simulate this
    conn = DatabaseOperations.get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            UPDATE orders 
            SET order_status = 'cancelled', updated_at = CURRENT_TIMESTAMP
            WHERE order_id = ? AND order_status IN ('pending', 'confirmed')
        ''', (order_id,))
        
        if cursor.rowcount > 0:
            conn.commit()
            conn.close()
            return True
        else:
            conn.close()
            return False
    except Exception as e:
        print(f"Error cancelling order: {e}")
        conn.close()
        return False

def show_rating_form(order_id):
    """Show order rating form"""
    with st.form(f"rating_form_{order_id}"):
        st.subheader("⭐ Rate Your Experience")
        
        rating = st.slider("Overall Rating", 1, 5, 5)
        delivery_rating = st.slider("Delivery Rating", 1, 5, 5)
        quality_rating = st.slider("Product Quality", 1, 5, 5)
        
        feedback = st.text_area("Additional Feedback (Optional)")
        
        if st.form_submit_button("Submit Rating"):
            # In a real app, save this to database
            st.success("Thank you for your feedback!")
            st.balloons()

def show_live_tracking(order_id):
    """Show live order tracking (simulation)"""
    st.subheader("📍 Live Tracking")
    
    order = DatabaseOperations.get_order_details(order_id)
    if not order:
        st.error("Order not found")
        return
    
    if order['order_status'] == 'out_for_delivery':
        # Simulate live tracking
        st.info("🚚 Your delivery partner is on the way!")
        
        # Mock delivery partner info
        st.write("**Delivery Partner:** Raj Kumar")
        st.write("**Contact:** +91 98765-43210")
        st.write("**Vehicle:** Bike (DL-01-AB-1234)")
        
        # Mock location updates
        locations = [
            "Left from store - Main Market",
            "Reached sector crossing",
            "Turning towards your street",
            "Arriving in 5 minutes"
        ]
        
        progress_step = min(3, len(locations) - 1)
        
        for i, location in enumerate(locations):
            if i <= progress_step:
                st.write(f"✅ {location}")
            else:
                st.write(f"⚪ {location}")
        
        # Mock map (placeholder)
        st.image("https://via.placeholder.com/400x200?text=Live+Map+Tracking", use_column_width=True)
        
        if st.button("📞 Call Delivery Partner"):
            st.info("Calling +91 98765-43210...")
    
    else:
        st.info("Live tracking will be available once your order is out for delivery")

def show_order_history_analytics():
    """Show user's order history analytics"""
    user = get_current_user()
    if not user:
        return
    
    orders = DatabaseOperations.get_user_orders(user['user_id'])
    
    if not orders:
        return
    
    st.subheader("📊 Your Shopping Analytics")
    
    # Basic stats
    total_orders = len(orders)
    total_spent = sum(order['total_amount'] for order in orders)
    avg_order_value = total_spent / total_orders if total_orders > 0 else 0
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Orders", total_orders)
    with col2:
        st.metric("Total Spent", f"₹{total_spent:.2f}")
    with col3:
        st.metric("Avg Order Value", f"₹{avg_order_value:.2f}")
    
    # Order status distribution
    if orders:
        order_statuses = [order['order_status'] for order in orders]
        status_counts = pd.Series(order_statuses).value_counts()
        
        if len(status_counts) > 1:
            st.bar_chart(status_counts)

def show_reorder_suggestions():
    """Show reorder suggestions based on order history"""
    user = get_current_user()
    if not user:
        return
    
    # Get recent orders for suggestions
    orders = DatabaseOperations.get_user_orders(user['user_id'])
    
    if not orders:
        return
    
    st.subheader("🔄 Reorder Your Favorites")
    
    # Get the most recent order for quick reorder
    recent_order = orders[0] if orders else None
    
    if recent_order:
        order_details = DatabaseOperations.get_order_details(recent_order['order_id'])
        
        if order_details:
            st.write(f"**Last Order:** {recent_order['order_id']} (₹{recent_order['total_amount']:.2f})")
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                # Show items from last order
                item_names = [item['name'] for item in order_details['items'][:3]]
                st.write(f"Items: {', '.join(item_names)}")
                if len(order_details['items']) > 3:
                    st.write(f"... and {len(order_details['items']) - 3} more items")
            
            with col2:
                if st.button("🔄 Reorder", key="reorder_last", use_container_width=True):
                    reorder_items(order_details['items'])

def get_order_status_badge(status):
    """Get styled status badge"""
    emoji = ORDER_STATUS_COLORS.get(status, '⚪')
    return f"{emoji} {status.replace('_', ' ').title()}"

def show_order_timeline():
    """Show user's complete order timeline"""
    user = get_current_user()
    if not user:
        return
    
    orders = DatabaseOperations.get_user_orders(user['user_id'])
    
    if not orders:
        return
    
    st.subheader("📅 Order Timeline")
    
    # Group orders by month
    monthly_orders = {}
    for order in orders:
        month_key = order['created_at'][:7]  # YYYY-MM
        if month_key not in monthly_orders:
            monthly_orders[month_key] = []
        monthly_orders[month_key].append(order)
    
    for month, month_orders in sorted(monthly_orders.items(), reverse=True):
        with st.expander(f"📅 {month} ({len(month_orders)} orders)"):
            for order in month_orders:
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.write(f"**{order['order_id']}**")
                    st.write(order['created_at'][:16])
                
                with col2:
                    st.write(get_order_status_badge(order['order_status']))
                
                with col3:
                    st.write(f"₹{order['total_amount']:.2f}")

def show_delivery_instructions():
    """Show delivery instructions and preferences"""
    st.subheader("📋 Delivery Preferences")
    
    user = get_current_user()
    if not user:
        return
    
    with st.form("delivery_preferences"):
        st.write("**Default Delivery Instructions:**")
        
        preferred_time = st.selectbox(
            "Preferred Delivery Time",
            ["Morning (9 AM - 12 PM)", "Afternoon (12 PM - 4 PM)", 
             "Evening (4 PM - 8 PM)", "Anytime"]
        )
        
        contact_preference = st.selectbox(
            "Contact Preference",
            ["Call before delivery", "Ring doorbell", "Leave at door", "Call on arrival"]
        )
        
        special_instructions = st.text_area(
            "Special Instructions",
            placeholder="e.g., Gate code, Building instructions, etc."
        )
        
        if st.form_submit_button("Save Preferences"):
            # In a real app, save these preferences to user profile
            st.success("Delivery preferences saved!")

def show_order_support():
    """Show order support options"""
    st.subheader("🆘 Need Help with Your Order?")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Common Issues:**")
        if st.button("🕐 Delayed Delivery", use_container_width=True):
            st.info("We'll check with our delivery team and update you shortly.")
        
        if st.button("📦 Missing Items", use_container_width=True):
            st.info("Please report missing items. We'll investigate and resolve within 24 hours.")
        
        if st.button("🔄 Return/Exchange", use_container_width=True):
            st.info("Returns accepted within 24 hours of delivery for fresh products.")
    
    with col2:
        st.write("**Contact Support:**")
        st.info("""
        📞 **Phone:** +91 9754373333
        📧 **Email:** support@radheradheandsons.com
        🕐 **Hours:** 9 AM - 9 PM (All days)
        
        **Prakhar Gupta** - Owner
        """)
        
        if st.button("💬 Start Chat Support", use_container_width=True):
            st.info("Chat support coming soon! Please call or email for immediate assistance.")
