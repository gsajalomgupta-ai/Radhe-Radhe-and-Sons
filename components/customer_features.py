import streamlit as st
from database.operations import DatabaseOperations
from utils.auth import get_current_user, logout_user
from components.order_management import show_reorder_suggestions, show_order_history_analytics

def show_profile_page():
    """Display user profile page"""
    st.title("👤 My Profile")
    
    user = get_current_user()
    if not user:
        st.warning("Please login to view your profile")
        return
    
    # Get full user details
    user_details = DatabaseOperations.get_user_by_id(user['user_id'])
    
    if not user_details:
        st.error("User details not found")
        return
    
    # Profile tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Personal Info", "📍 Addresses", "🏆 Loyalty", "⚙️ Settings"])
    
    with tab1:
        show_personal_info(user_details)
    
    with tab2:
        show_address_management(user['user_id'])
    
    with tab3:
        show_loyalty_program(user_details)
    
    with tab4:
        show_account_settings(user_details)

def show_personal_info(user_details):
    """Show and edit personal information"""
    st.subheader("📋 Personal Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Current Information:**")
        st.info(f"""
        **Name:** {user_details['name']}
        **Phone:** {user_details['phone']}
        **Email:** {user_details.get('email', 'Not provided')}
        **Loyalty Points:** {user_details['loyalty_points']}
        """)
    
    with col2:
        st.write("**Update Information:**")
        with st.form("update_profile"):
            new_name = st.text_input("Full Name", value=user_details['name'])
            new_email = st.text_input("Email", value=user_details.get('email', ''))
            
            if st.form_submit_button("💾 Update Profile"):
                # Update user information
                conn = DatabaseOperations.get_db_connection()
                cursor = conn.cursor()
                
                try:
                    cursor.execute('''
                        UPDATE users SET name = ?, email = ? WHERE user_id = ?
                    ''', (new_name, new_email, user_details['user_id']))
                    conn.commit()
                    st.success("Profile updated successfully!")
                    
                    # Update session state
                    st.session_state.user['name'] = new_name
                    st.session_state.user['email'] = new_email
                    st.rerun()
                except Exception as e:
                    st.error(f"Error updating profile: {e}")
                finally:
                    conn.close()

def show_address_management(user_id):
    """Address management interface"""
    st.subheader("📍 Delivery Addresses")
    
    addresses = DatabaseOperations.get_user_addresses(user_id)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.write("**Saved Addresses:**")
        
        if addresses:
            for addr in addresses:
                with st.container():
                    col_addr1, col_addr2, col_addr3 = st.columns([2, 1, 1])
                    
                    with col_addr1:
                        default_badge = " 🏠 (Default)" if addr['is_default'] else ""
                        st.write(f"**{addr['address_type']}{default_badge}**")
                        st.write(f"{addr['full_address']}")
                        if addr['landmark']:
                            st.write(f"Landmark: {addr['landmark']}")
                        st.write(f"PIN: {addr['pincode']}")
                    
                    with col_addr2:
                        if not addr['is_default'] and st.button("Set Default", key=f"default_{addr['id']}"):
                            set_default_address(user_id, addr['id'])
                            st.rerun()
                    
                    with col_addr3:
                        if st.button("🗑️ Delete", key=f"del_addr_{addr['id']}"):
                            delete_address(addr['id'])
                            st.rerun()
                
                st.divider()
        else:
            st.info("No addresses saved yet")
    
    with col2:
        st.write("**Add New Address:**")
        show_add_address_form(user_id)

def show_add_address_form(user_id):
    """Form to add new address"""
    with st.form("add_address"):
        address_type = st.selectbox("Address Type", ["Home", "Office", "Other"])
        full_address = st.text_area("Full Address", placeholder="House/Flat No, Street, Area")
        landmark = st.text_input("Landmark (Optional)", placeholder="Near landmark")
        pincode = st.text_input("Pincode", placeholder="6-digit pincode")
        is_default = st.checkbox("Set as default address")
        
        if st.form_submit_button("➕ Add Address", use_container_width=True):
            if full_address and pincode:
                DatabaseOperations.add_user_address(
                    user_id, address_type, full_address, landmark, pincode, is_default
                )
                st.success("Address added successfully!")
                st.rerun()
            else:
                st.error("Please fill required fields")

def set_default_address(user_id, address_id):
    """Set an address as default"""
    conn = DatabaseOperations.get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Remove default from all addresses
        cursor.execute('UPDATE user_addresses SET is_default = FALSE WHERE user_id = ?', (user_id,))
        
        # Set new default
        cursor.execute('UPDATE user_addresses SET is_default = TRUE WHERE id = ?', (address_id,))
        
        conn.commit()
        st.success("Default address updated!")
    except Exception as e:
        st.error(f"Error updating address: {e}")
    finally:
        conn.close()

def delete_address(address_id):
    """Delete an address"""
    conn = DatabaseOperations.get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('DELETE FROM user_addresses WHERE id = ?', (address_id,))
        conn.commit()
        st.success("Address deleted!")
    except Exception as e:
        st.error(f"Error deleting address: {e}")
    finally:
        conn.close()

def show_loyalty_program(user_details):
    """Show loyalty program information"""
    st.subheader("🏆 Loyalty Program")
    
    loyalty_points = user_details['loyalty_points']
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.metric("Your Points", loyalty_points)
        
        # Calculate tier
        if loyalty_points >= 1000:
            tier = "🥇 Gold"
            next_tier_points = 2000
        elif loyalty_points >= 500:
            tier = "🥈 Silver"
            next_tier_points = 1000
        else:
            tier = "🥉 Bronze"
            next_tier_points = 500
        
        st.write(f"**Current Tier:** {tier}")
        
        points_to_next = next_tier_points - loyalty_points
        if points_to_next > 0:
            st.write(f"**Points to next tier:** {points_to_next}")
            st.progress(loyalty_points / next_tier_points)
    
    with col2:
        st.write("**How to earn points:**")
        st.write("• 1 point for every ₹10 spent")
        st.write("• 50 bonus points on first order")
        st.write("• 25 points for each referral")
        st.write("• 100 points on birthday month")
        
        st.write("**Redeem points:**")
        st.write("• 100 points = ₹10 discount")
        st.write("• 500 points = ₹60 discount")
        st.write("• 1000 points = ₹150 discount")
        
        redeemable_points = (loyalty_points // 100) * 100
        if redeemable_points >= 100:
            if st.button(f"🎁 Redeem {redeemable_points} points", use_container_width=True):
                st.info("Points redemption coming soon!")

def show_account_settings(user_details):
    """Show account settings"""
    st.subheader("⚙️ Account Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Notification Preferences:**")
        
        with st.form("notification_settings"):
            email_notifications = st.checkbox("Email Notifications", value=True)
            sms_notifications = st.checkbox("SMS Notifications", value=True)
            push_notifications = st.checkbox("Push Notifications", value=True)
            promotional_emails = st.checkbox("Promotional Emails", value=False)
            
            if st.form_submit_button("💾 Save Preferences"):
                st.success("Notification preferences saved!")
        
        st.write("**Privacy Settings:**")
        with st.form("privacy_settings"):
            share_data = st.checkbox("Share data for personalized recommendations", value=True)
            marketing_consent = st.checkbox("Receive marketing communications", value=False)
            
            if st.form_submit_button("💾 Save Privacy Settings"):
                st.success("Privacy settings saved!")
    
    with col2:
        st.write("**Account Actions:**")
        
        if st.button("🔐 Change Password", use_container_width=True):
            show_change_password_form(user_details['user_id'])
        
        if st.button("📥 Download My Data", use_container_width=True):
            st.info("Data download functionality coming soon!")
        
        if st.button("🚪 Logout", use_container_width=True):
            logout_user()
            st.success("Logged out successfully!")
            st.rerun()
        
        st.write("---")
        st.write("**⚠️ Danger Zone:**")
        if st.button("🗑️ Delete Account", use_container_width=True, type="secondary"):
            show_delete_account_confirmation()

def show_change_password_form(user_id):
    """Show change password form"""
    with st.form("change_password"):
        st.subheader("🔐 Change Password")
        
        current_password = st.text_input("Current Password", type="password")
        new_password = st.text_input("New Password", type="password")
        confirm_password = st.text_input("Confirm New Password", type="password")
        
        if st.form_submit_button("🔄 Change Password"):
            if not all([current_password, new_password, confirm_password]):
                st.error("Please fill all fields")
                return
            
            if new_password != confirm_password:
                st.error("New passwords do not match")
                return
            
            if len(new_password) < 6:
                st.error("Password must be at least 6 characters long")
                return
            
            # Verify current password and update
            # For demo, just show success
            st.success("Password changed successfully!")

def show_delete_account_confirmation():
    """Show account deletion confirmation"""
    st.error("⚠️ **Delete Account**")
    st.write("This action cannot be undone. All your data will be permanently deleted.")
    
    with st.form("delete_account"):
        confirmation = st.text_input("Type 'DELETE' to confirm")
        
        if st.form_submit_button("🗑️ Permanently Delete Account", type="secondary"):
            if confirmation == "DELETE":
                st.error("Account deletion functionality is disabled in demo mode")
            else:
                st.error("Please type 'DELETE' to confirm")

def show_order_history_page():
    """Enhanced order history page"""
    st.title("📦 Order History")
    
    user = get_current_user()
    if not user:
        st.warning("Please login to view your order history")
        return
    
    # Show analytics first
    show_order_history_analytics()
    
    # Show reorder suggestions
    show_reorder_suggestions()
    
    # Import and show orders
    from components.order_management import show_orders_page
    show_orders_page()

def show_favorites_page():
    """Show user's favorite products"""
    st.title("❤️ My Favorites")
    
    user = get_current_user()
    if not user:
        st.warning("Please login to view your favorites")
        return
    
    # Get user favorites
    conn = DatabaseOperations.get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT p.product_id, p.name, p.price, p.unit, p.image_url, p.stock_quantity
        FROM favorites f
        JOIN products p ON f.product_id = p.product_id
        WHERE f.user_id = ? AND p.is_active = TRUE
        ORDER BY f.added_at DESC
    ''', (user['user_id'],))
    
    favorites = cursor.fetchall()
    conn.close()
    
    if favorites:
        st.write(f"You have {len(favorites)} favorite products")
        
        # Display favorites grid
        cols = st.columns(3)
        
        for idx, fav in enumerate(favorites):
            col_idx = idx % 3
            
            with cols[col_idx]:
                st.image(
                    fav[4] if fav[4] else 'https://via.placeholder.com/150x100?text=No+Image',
                    use_column_width=True
                )
                st.write(f"**{fav[1]}**")  # name
                st.write(f"₹{fav[2]:.2f}/{fav[3]}")  # price/unit
                
                col_fav1, col_fav2 = st.columns(2)
                
                with col_fav1:
                    if st.button("🛒 Add to Cart", key=f"fav_add_{fav[0]}", use_container_width=True):
                        if DatabaseOperations.add_to_cart(user['user_id'], fav[0], 1):
                            st.success("Added to cart!")
                            from utils.auth import update_cart_count
                            update_cart_count()
                            st.rerun()
                
                with col_fav2:
                    if st.button("💔 Remove", key=f"fav_remove_{fav[0]}", use_container_width=True):
                        remove_from_favorites(user['user_id'], fav[0])
                        st.rerun()
    else:
        st.info("You haven't added any favorites yet!")
        
        if st.button("🛍️ Browse Products", use_container_width=True):
            st.session_state.current_page = 'products'
            st.rerun()

def add_to_favorites(user_id, product_id):
    """Add product to favorites"""
    conn = DatabaseOperations.get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT OR IGNORE INTO favorites (user_id, product_id)
            VALUES (?, ?)
        ''', (user_id, product_id))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error adding to favorites: {e}")
        return False
    finally:
        conn.close()

def remove_from_favorites(user_id, product_id):
    """Remove product from favorites"""
    conn = DatabaseOperations.get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            DELETE FROM favorites WHERE user_id = ? AND product_id = ?
        ''', (user_id, product_id))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error removing from favorites: {e}")
        return False
    finally:
        conn.close()

def show_support_page():
    """Show customer support page"""
    st.title("🆘 Customer Support")
    
    # Contact information
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📞 Contact Us")
        st.info("""
        **📞 Phone:** +91 9754373333
        **📧 Email:** support@radheradheandsons.com
        **🕐 Hours:** 9 AM - 9 PM (All days)
        
        **Owner:** Prakhar Gupta
        **Address:** Main Market, City
        """)
        
        # Quick actions
        if st.button("📞 Call Now", use_container_width=True):
            st.info("Calling +91 9754373333...")
        
        if st.button("📧 Send Email", use_container_width=True):
            st.info("Opening email client...")
    
    with col2:
        st.subheader("💬 Send Message")
        
        with st.form("support_message"):
            subject = st.selectbox(
                "Subject",
                ["General Inquiry", "Order Issue", "Payment Problem", 
                 "Delivery Issue", "Product Quality", "Refund Request", "Other"]
            )
            
            if subject == "Order Issue":
                order_id = st.text_input("Order ID (if applicable)")
            
            message = st.text_area("Your Message", placeholder="Describe your issue or question...")
            
            if st.form_submit_button("📤 Send Message", use_container_width=True):
                if message:
                    st.success("Message sent successfully! We'll respond within 24 hours.")
                else:
                    st.error("Please enter your message")
    
    # FAQ Section
    st.subheader("❓ Frequently Asked Questions")
    
    faqs = [
        {
            "question": "What are your delivery hours?",
            "answer": "We deliver from 9 AM to 9 PM, 7 days a week. Orders placed before 8 PM are delivered the same day."
        },
        {
            "question": "What is your delivery radius?",
            "answer": "We currently deliver within 5 km radius of our store. Free delivery on orders above ₹500."
        },
        {
            "question": "How can I track my order?",
            "answer": "You can track your order in real-time from the 'My Orders' section. You'll also receive SMS updates."
        },
        {
            "question": "What is your return policy?",
            "answer": "We accept returns within 24 hours of delivery for fresh products. Packaged items can be returned if unopened."
        },
        {
            "question": "How do I earn loyalty points?",
            "answer": "Earn 1 point for every ₹10 spent. Redeem 100 points for ₹10 discount on your next order."
        }
    ]
    
    for faq in faqs:
        with st.expander(f"❓ {faq['question']}"):
            st.write(faq['answer'])

def show_referral_program():
    """Show referral program"""
    st.subheader("🎁 Refer & Earn")
    
    user = get_current_user()
    if not user:
        return
    
    # Generate referral code (for demo)
    referral_code = f"RRS{user['user_id'][:8].upper()}"
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Your Referral Code:**")
        st.code(referral_code, language=None)
        
        if st.button("📋 Copy Code", use_container_width=True):
            st.success("Referral code copied!")
        
        st.write("**How it works:**")
        st.write("• Share your code with friends")
        st.write("• They get ₹50 off on first order")
        st.write("• You get 100 loyalty points")
        st.write("• Minimum order value: ₹200")
    
    with col2:
        st.write("**Your Referral Stats:**")
        # Mock referral stats
        st.metric("Friends Referred", 3)
        st.metric("Points Earned", 300)
        st.metric("Total Savings Generated", "₹150")
        
        st.write("**Share via:**")
        col_share1, col_share2 = st.columns(2)
        
        with col_share1:
            if st.button("📱 WhatsApp", use_container_width=True):
                st.info("Opening WhatsApp...")
        
        with col_share2:
            if st.button("📧 Email", use_container_width=True):
                st.info("Opening email client...")

def show_notifications_page():
    """Show user notifications"""
    st.title("🔔 Notifications")
    
    user = get_current_user()
    if not user:
        st.warning("Please login to view notifications")
        return
    
    # Mock notifications
    notifications = [
        {
            "title": "Order Delivered",
            "message": "Your order #RRS20241221ABC123 has been delivered successfully!",
            "time": "2 hours ago",
            "type": "success"
        },
        {
            "title": "New Offer Available",
            "message": "Get 20% off on fruits and vegetables. Use code FRESH20",
            "time": "1 day ago",
            "type": "info"
        },
        {
            "title": "Order Confirmed",
            "message": "Your order #RRS20241220XYZ456 has been confirmed and will be delivered soon.",
            "time": "2 days ago",
            "type": "success"
        }
    ]
    
    for notif in notifications:
        if notif['type'] == 'success':
            st.success(f"**{notif['title']}** - {notif['time']}\n\n{notif['message']}")
        elif notif['type'] == 'info':
            st.info(f"**{notif['title']}** - {notif['time']}\n\n{notif['message']}")
        else:
            st.warning(f"**{notif['title']}** - {notif['time']}\n\n{notif['message']}")
    
    # Clear all notifications
    if st.button("🗑️ Clear All Notifications", use_container_width=True):
        st.success("All notifications cleared!")
        st.rerun()
