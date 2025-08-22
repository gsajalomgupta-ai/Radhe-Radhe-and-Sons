import streamlit as st
from database.operations import DatabaseOperations
from utils.auth import get_current_user, update_cart_count

# Coupon codes for demo
COUPON_CODES = {
    'WELCOME10': {'discount_type': 'percentage', 'discount_value': 10, 'min_order': 200},
    'FLAT50': {'discount_type': 'flat', 'discount_value': 50, 'min_order': 300},
    'FIRST20': {'discount_type': 'percentage', 'discount_value': 20, 'min_order': 150}
}

def calculate_discount(subtotal, coupon_code):
    """Calculate discount amount based on coupon code"""
    if not coupon_code or coupon_code not in COUPON_CODES:
        return 0, "Invalid coupon code"
    
    coupon = COUPON_CODES[coupon_code]
    
    if subtotal < coupon['min_order']:
        return 0, f"Minimum order value ₹{coupon['min_order']} required"
    
    if coupon['discount_type'] == 'percentage':
        discount = subtotal * (coupon['discount_value'] / 100)
    else:  # flat discount
        discount = coupon['discount_value']
    
    return min(discount, subtotal), "Coupon applied successfully!"

def show_cart_page():
    """Display shopping cart page"""
    st.title("🛒 Shopping Cart")
    
    user = get_current_user()
    if not user:
        st.warning("Please login to view your cart")
        return
    
    cart_items = DatabaseOperations.get_cart_items(user['user_id'])
    
    if not cart_items:
        st.info("Your cart is empty! 🛒")
        if st.button("Start Shopping", use_container_width=True):
            st.session_state.current_page = 'products'
            st.rerun()
        return
    
    # Display cart items
    st.subheader("Items in your cart")
    
    total_amount = 0
    
    for item in cart_items:
        col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])
        
        with col1:
            st.write(f"**{item['name']}**")
            st.write(f"₹{item['price']}/{item['unit']}")
        
        with col2:
            st.image(
                item.get('image_url', 'https://via.placeholder.com/80x60?text=No+Image'),
                width=80
            )
        
        with col3:
            new_quantity = st.number_input(
                "Qty",
                min_value=0,
                max_value=10,
                value=item['quantity'],
                key=f"cart_qty_{item['product_id']}",
                label_visibility="collapsed"
            )
            
            if new_quantity != item['quantity']:
                DatabaseOperations.update_cart_quantity(
                    user['user_id'], 
                    item['product_id'], 
                    new_quantity
                )
                update_cart_count()
                st.rerun()
        
        with col4:
            st.write(f"₹{item['total_price']:.2f}")
        
        with col5:
            if st.button("🗑️", key=f"remove_{item['product_id']}", help="Remove from cart"):
                DatabaseOperations.update_cart_quantity(user['user_id'], item['product_id'], 0)
                update_cart_count()
                st.rerun()
        
        total_amount += item['total_price']
        st.divider()
    
    # Cart summary
    show_cart_summary(total_amount, user)

def show_cart_summary(subtotal, user):
    """Show cart summary and checkout"""
    st.subheader("💰 Order Summary")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Coupon code section
        with st.expander("🎫 Have a coupon code?"):
            coupon_code = st.text_input("Enter coupon code", key="coupon_input")
            apply_coupon = st.button("Apply Coupon")
            
            discount_amount = 0
            coupon_message = ""
            
            if apply_coupon and coupon_code:
                discount_amount, coupon_message = calculate_discount(subtotal, coupon_code.upper())
                if discount_amount > 0:
                    st.success(coupon_message)
                    st.session_state.applied_coupon = coupon_code.upper()
                    st.session_state.discount_amount = discount_amount
                else:
                    st.error(coupon_message)
        
        # Use saved discount if available
        if 'applied_coupon' in st.session_state:
            discount_amount = st.session_state.get('discount_amount', 0)
            st.success(f"Coupon {st.session_state.applied_coupon} applied! Saved ₹{discount_amount:.2f}")
    
    with col2:
        # Order summary
        delivery_charges = 30 if subtotal < 500 else 0
        total_amount = subtotal + delivery_charges - discount_amount
        
        st.write(f"**Subtotal:** ₹{subtotal:.2f}")
        if discount_amount > 0:
            st.write(f"**Discount:** -₹{discount_amount:.2f}")
        st.write(f"**Delivery:** ₹{delivery_charges:.2f}")
        if subtotal >= 500:
            st.caption("Free delivery on orders ₹500+")
        st.write(f"**Total:** ₹{total_amount:.2f}")
        
        if st.button("🚀 Proceed to Checkout", use_container_width=True, type="primary"):
            st.session_state.checkout_total = total_amount
            st.session_state.checkout_subtotal = subtotal
            st.session_state.checkout_delivery = delivery_charges
            st.session_state.checkout_discount = discount_amount
            st.session_state.current_page = 'checkout'
            st.rerun()

def show_checkout_page():
    """Display checkout page"""
    st.title("🚀 Checkout")
    
    user = get_current_user()
    if not user:
        st.warning("Please login to checkout")
        return
    
    # Get checkout totals from session state
    total_amount = st.session_state.get('checkout_total', 0)
    subtotal = st.session_state.get('checkout_subtotal', 0)
    delivery_charges = st.session_state.get('checkout_delivery', 0)
    discount_amount = st.session_state.get('checkout_discount', 0)
    
    if total_amount == 0:
        st.error("No items in checkout. Please add items to cart first.")
        return
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Delivery address section
        st.subheader("📍 Delivery Address")
        
        # Get user addresses
        addresses = DatabaseOperations.get_user_addresses(user['user_id'])
        
        if addresses:
            address_options = [
                f"{addr['address_type']}: {addr['full_address'][:50]}..." 
                for addr in addresses
            ]
            selected_addr_idx = st.selectbox(
                "Choose delivery address",
                range(len(address_options)),
                format_func=lambda x: address_options[x]
            )
            selected_address = addresses[selected_addr_idx]
            delivery_address = f"{selected_address['full_address']}, {selected_address['landmark']}, {selected_address['pincode']}"
        else:
            st.info("No saved addresses found. Please add a delivery address.")
            with st.form("add_address_form"):
                address_type = st.selectbox("Address Type", ["Home", "Office", "Other"])
                full_address = st.text_area("Full Address")
                landmark = st.text_input("Landmark (Optional)")
                pincode = st.text_input("Pincode")
                
                if st.form_submit_button("Save Address"):
                    if full_address and pincode:
                        DatabaseOperations.add_user_address(
                            user['user_id'], address_type, full_address, landmark, pincode, True
                        )
                        st.success("Address saved!")
                        st.rerun()
                    else:
                        st.error("Please fill required fields")
            return
        
        # Contact number
        st.subheader("📞 Contact Number")
        phone = st.text_input("Phone Number", value=user.get('phone', ''), disabled=True)
        
        # Payment method
        st.subheader("💳 Payment Method")
        payment_method = st.selectbox(
            "Choose payment method",
            ["UPI", "Debit/Credit Card", "Net Banking", "Cash on Delivery", "Wallet"]
        )
        
        # Special instructions
        st.subheader("📝 Special Instructions (Optional)")
        special_instructions = st.text_area(
            "Any special delivery instructions",
            placeholder="e.g., Ring the doorbell twice, Leave at door, etc."
        )
    
    with col2:
        # Order summary
        st.subheader("📄 Order Summary")
        
        # Get cart items for display
        cart_items = DatabaseOperations.get_cart_items(user['user_id'])
        
        for item in cart_items:
            st.write(f"**{item['name']}** x{item['quantity']}")
            st.write(f"₹{item['total_price']:.2f}")
            st.divider()
        
        st.write(f"**Subtotal:** ₹{subtotal:.2f}")
        if discount_amount > 0:
            st.write(f"**Discount:** -₹{discount_amount:.2f}")
        st.write(f"**Delivery:** ₹{delivery_charges:.2f}")
        st.write(f"**Total:** ₹{total_amount:.2f}")
        
        # Place order button
        if st.button("🎯 Place Order", use_container_width=True, type="primary"):
            if 'delivery_address' not in locals():
                st.error("Please select a delivery address")
                return
            
            # Create order
            order_id = DatabaseOperations.create_order(
                user_id=user['user_id'],
                delivery_address=delivery_address,
                phone=phone,
                payment_method=payment_method,
                cart_items=cart_items,
                total_amount=total_amount,
                delivery_charges=delivery_charges,
                discount_amount=discount_amount,
                coupon_code=st.session_state.get('applied_coupon')
            )
            
            if order_id:
                st.success(f"🎉 Order placed successfully!")
                st.balloons()
                st.info(f"Order ID: **{order_id}**")
                
                # Clear checkout session data
                for key in ['checkout_total', 'checkout_subtotal', 'checkout_delivery', 
                           'checkout_discount', 'applied_coupon', 'discount_amount']:
                    if key in st.session_state:
                        del st.session_state[key]
                
                update_cart_count()
                
                # Redirect to order confirmation
                st.session_state.current_page = 'orders'
                st.session_state.order_placed = order_id
                st.rerun()
            else:
                st.error("Failed to place order. Please try again.")

def show_cart_icon_with_count():
    """Show cart icon with item count for navigation"""
    cart_count = st.session_state.get('cart_count', 0)
    
    if cart_count > 0:
        return f"🛒 Cart ({cart_count})"
    else:
        return "🛒 Cart"

def show_mini_cart():
    """Show mini cart in sidebar"""
    user = get_current_user()
    if not user:
        return
    
    st.sidebar.subheader("🛒 Your Cart")
    
    cart_items = DatabaseOperations.get_cart_items(user['user_id'])
    
    if not cart_items:
        st.sidebar.info("Cart is empty")
        return
    
    total = sum(item['total_price'] for item in cart_items)
    
    # Show first 3 items
    for item in cart_items[:3]:
        st.sidebar.write(f"**{item['name']}** x{item['quantity']}")
        st.sidebar.write(f"₹{item['total_price']:.2f}")
        st.sidebar.write("---")
    
    if len(cart_items) > 3:
        st.sidebar.write(f"... and {len(cart_items) - 3} more items")
    
    st.sidebar.write(f"**Total: ₹{total:.2f}**")
    
    if st.sidebar.button("View Full Cart", use_container_width=True):
        st.session_state.current_page = 'cart'
        st.rerun()

def show_quick_add_suggestions():
    """Show quick add suggestions based on popular items"""
    st.subheader("🔥 Popular Items")
    st.caption("Frequently bought together")
    
    # Get some popular products (for demo, just get first 4)
    popular_products = DatabaseOperations.get_products(limit=4)
    
    cols = st.columns(4)
    
    for idx, product in enumerate(popular_products):
        with cols[idx]:
            st.image(
                product.get('image_url', 'https://via.placeholder.com/100x80?text=No+Image'),
                width=100
            )
            st.write(f"**{product['name']}**")
            st.write(f"₹{product['price']}/{product['unit']}")
            
            if st.button(f"Quick Add", key=f"quick_add_{product['product_id']}", use_container_width=True):
                user = get_current_user()
                if user:
                    if DatabaseOperations.add_to_cart(user['user_id'], product['product_id'], 1):
                        st.success("Added to cart!")
                        update_cart_count()
                        st.rerun()
                else:
                    st.warning("Please login first")

def show_order_confirmation(order_id):
    """Show order confirmation page"""
    st.title("✅ Order Confirmed!")
    
    order_details = DatabaseOperations.get_order_details(order_id)
    
    if not order_details:
        st.error("Order not found")
        return
    
    # Order success message
    st.success(f"""
    🎉 **Your order has been placed successfully!**
    
    **Order ID:** {order_details['order_id']}
    **Total Amount:** ₹{order_details['total_amount']:.2f}
    **Payment Method:** {order_details['payment_method']}
    **Estimated Delivery:** {order_details['estimated_delivery']}
    """)
    
    # Order items
    st.subheader("📦 Order Items")
    for item in order_details['items']:
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.write(f"**{item['name']}**")
        with col2:
            st.write(f"Qty: {item['quantity']}")
        with col3:
            st.write(f"₹{item['price'] * item['quantity']:.2f}")
    
    # Delivery information
    st.subheader("🚚 Delivery Information")
    st.info(f"""
    **Delivery Address:** {order_details['delivery_address']}
    **Contact Number:** {order_details['phone']}
    **Estimated Delivery Time:** 60-120 minutes
    """)
    
    # Action buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📱 Track Order", use_container_width=True):
            st.session_state.current_page = 'orders'
            st.session_state.track_order_id = order_id
            st.rerun()
    
    with col2:
        if st.button("🛍️ Continue Shopping", use_container_width=True):
            st.session_state.current_page = 'products'
            st.rerun()
    
    with col3:
        if st.button("📞 Customer Support", use_container_width=True):
            st.info("📞 Call: +91 9754373333\n📧 Email: support@radheradheandsons.com")

def show_empty_cart_message():
    """Show empty cart with suggestions"""
    st.title("🛒 Your cart is empty")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.image("https://via.placeholder.com/300x200?text=Empty+Cart", use_column_width=True)
        st.markdown("### Start adding items to your cart!")
        
        if st.button("🛍️ Browse Products", use_container_width=True, type="primary"):
            st.session_state.current_page = 'products'
            st.rerun()
    
    # Show popular items for quick add
    show_quick_add_suggestions()
