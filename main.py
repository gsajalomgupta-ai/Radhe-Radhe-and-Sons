import streamlit as st
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.models import init_database
from utils.auth import (
    init_session_state, get_current_user, is_admin, 
    show_auth_page, logout_user, update_cart_count
)
from components.product_catalog import (
    show_product_catalog, show_category_showcase, 
    show_featured_products
)
from components.cart_checkout import (
    show_cart_page, show_checkout_page, show_cart_icon_with_count,
    show_mini_cart
)
from components.order_management import show_orders_page
from components.admin_dashboard import show_admin_dashboard
from components.customer_features import (
    show_profile_page, show_favorites_page, show_support_page
)

# Page configuration
st.set_page_config(
    page_title="Radhe Radhe & Sons - Grocery Delivery",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #2E7D32, #4CAF50);
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
    }
    
    .nav-button {
        background: #E8F5E8;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        margin: 0.2rem;
        cursor: pointer;
    }
    
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #E8F5E8, #F1F8E9);
    }
    
    .stButton > button {
        border-radius: 10px;
        border: none;
        background: linear-gradient(45deg, #4CAF50, #66BB6A);
        color: white;
    }
    
    .stButton > button:hover {
        background: linear-gradient(45deg, #66BB6A, #81C784);
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(76,175,80,0.3);
    }
</style>
""", unsafe_allow_html=True)

def main():
    """Main application function"""
    # Initialize database and session state
    init_database()
    init_session_state()
    
    # Show header
    show_header()
    
    # Show navigation
    show_navigation()
    
    # Show main content based on current page
    current_page = st.session_state.get('current_page', 'home')
    
    if current_page == 'home':
        show_home_page()
    elif current_page == 'products':
        show_product_catalog()
    elif current_page == 'cart':
        show_cart_page()
    elif current_page == 'checkout':
        show_checkout_page()
    elif current_page == 'orders':
        show_orders_page()
    elif current_page == 'profile':
        show_profile_page()
    elif current_page == 'favorites':
        show_favorites_page()
    elif current_page == 'support':
        show_support_page()
    elif current_page == 'admin':
        show_admin_dashboard()
    elif current_page == 'auth':
        show_auth_page()
    
    # Show sidebar
    show_sidebar()

def show_header():
    """Show application header"""
    st.markdown("""
    <div class="main-header">
        <h1>🛒 Radhe Radhe & Sons</h1>
        <p>Fresh Groceries Delivered to Your Doorstep</p>
        <p>📞 +91 9754373333 | Owner: Prakhar Gupta</p>
    </div>
    """, unsafe_allow_html=True)

def show_navigation():
    """Show main navigation"""
    user = get_current_user()
    
    # Navigation bar
    col1, col2, col3, col4, col5, col6, col7, col8 = st.columns([1, 1, 1, 1, 1, 1, 1, 2])
    
    with col1:
        if st.button("🏠 Home"):
            st.session_state.current_page = 'home'
            st.rerun()
    
    with col2:
        if st.button("🛍️ Products"):
            st.session_state.current_page = 'products'
            st.rerun()
    
    with col3:
        cart_label = show_cart_icon_with_count()
        if st.button(cart_label):
            st.session_state.current_page = 'cart'
            st.rerun()
    
    with col4:
        if user:
            if st.button("📦 My Orders"):
                st.session_state.current_page = 'orders'
                st.rerun()
        else:
            st.write("")
    
    with col5:
        if user:
            if st.button("👤 Profile"):
                st.session_state.current_page = 'profile'
                st.rerun()
        else:
            st.write("")
    
    with col6:
        if user and is_admin():
            if st.button("🔧 Admin"):
                st.session_state.current_page = 'admin'
                st.rerun()
        else:
            st.write("")
    
    with col7:
        if st.button("🆘 Support"):
            st.session_state.current_page = 'support'
            st.rerun()
    
    with col8:
        if user:
            col_user1, col_user2 = st.columns([3, 1])
            with col_user1:
                st.write(f"Welcome, **{user['name']}**!")
            with col_user2:
                if st.button("🚪"):
                    logout_user()
                    st.rerun()
        else:
            if st.button("🔐 Login/Register", use_container_width=True):
                st.session_state.current_page = 'auth'
                st.rerun()

def show_home_page():
    """Show home page"""
    user = get_current_user()
    
    # Welcome message
    if user:
        st.subheader(f"Welcome back, {user['name']}! 👋")
    else:
        st.subheader("Welcome to Radhe Radhe & Sons! 🛒")
        st.info("Please login to start shopping and enjoy personalized experience")
    
    # Store highlights
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("⚡ Delivery Time", "30-90 mins")
    with col2:
        st.metric("🚚 Free Delivery", "On ₹500+")
    with col3:
        st.metric("📱 Customer Support", "9 AM - 9 PM")
    with col4:
        st.metric("🎯 Delivery Radius", "5 km")
    
    # Special offers banner
    st.markdown("""
    <div style='background: linear-gradient(45deg, #FF6B6B, #FF8E8E); color: white; 
                padding: 20px; border-radius: 10px; text-align: center; margin: 20px 0;'>
        <h2>🎉 Special Offers Today!</h2>
        <p><strong>WELCOME10</strong> - Get 10% off on orders above ₹200</p>
        <p><strong>FLAT50</strong> - Flat ₹50 off on orders above ₹300</p>
        <p><strong>FIRST20</strong> - 20% off for new customers (min order ₹150)</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Category showcase
    show_category_showcase()
    
    # Featured products
    show_featured_products()
    
    # Customer testimonials
    show_customer_testimonials()
    
    # Store information
    show_store_info()

def show_sidebar():
    """Show application sidebar"""
    user = get_current_user()
    
    # Mini cart
    if user:
        show_mini_cart()
    
    # Store information
    st.sidebar.markdown("---")
    st.sidebar.subheader("🏪 Store Info")
    st.sidebar.info("""
    **Radhe Radhe & Sons**
    Fresh Groceries & Daily Needs
    
    📞 +91 9754373333
    👤 Prakhar Gupta (Owner)
    🕐 9 AM - 9 PM (All Days)
    🚚 Delivery: 30-90 minutes
    """)
    
    # Quick links
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔗 Quick Links")
    
    if st.sidebar.button("🎁 Refer & Earn", use_container_width=True):
        if user:
            from components.customer_features import show_referral_program
            show_referral_program()
        else:
            st.warning("Please login to access referral program")
    
    if st.sidebar.button("❓ FAQs", use_container_width=True):
        st.session_state.current_page = 'support'
        st.rerun()
    
    # App info
    st.sidebar.markdown("---")
    st.sidebar.caption("Radhe Radhe & Sons Grocery App v1.0")
    st.sidebar.caption("Built with ❤️ using Streamlit")

def show_customer_testimonials():
    """Show customer testimonials"""
    st.subheader("💬 What Our Customers Say")
    
    testimonials = [
        {
            "name": "Priya Sharma",
            "rating": 5,
            "comment": "Great quality products and super fast delivery! Highly recommended.",
            "location": "Sector 21"
        },
        {
            "name": "Rajesh Kumar", 
            "rating": 5,
            "comment": "Fresh vegetables and fruits. The app is very user-friendly.",
            "location": "Civil Lines"
        },
        {
            "name": "Anjali Gupta",
            "rating": 4,
            "comment": "Good service and reasonable prices. Will order again!",
            "location": "Model Town"
        }
    ]
    
    cols = st.columns(3)
    
    for idx, testimonial in enumerate(testimonials):
        with cols[idx]:
            stars = "⭐" * testimonial['rating']
            st.markdown(f"""
            <div style='border: 1px solid #ddd; border-radius: 10px; padding: 15px; 
                        background: #F8F9FA; margin: 10px 0;'>
                <p><strong>{testimonial['name']}</strong> - {testimonial['location']}</p>
                <p>{stars}</p>
                <p style='font-style: italic;'>"{testimonial['comment']}"</p>
            </div>
            """, unsafe_allow_html=True)

def show_store_info():
    """Show store information and policies"""
    st.subheader("🏪 About Radhe Radhe & Sons")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.write("**📋 Our Promise**")
        st.write("✅ Fresh & Quality Products")
        st.write("✅ Fastest Delivery")
        st.write("✅ Best Prices Guaranteed")
        st.write("✅ 100% Satisfaction")
    
    with col2:
        st.write("**🚚 Delivery Info**")
        st.write("• Delivery Radius: 5 km")
        st.write("• Delivery Time: 30-90 minutes")
        st.write("• Free delivery on ₹500+")
        st.write("• Cash on Delivery available")
    
    with col3:
        st.write("**💳 Payment Methods**")
        st.write("• UPI (PhonePe, GPay, Paytm)")
        st.write("• Debit/Credit Cards")
        st.write("• Net Banking")
        st.write("• Cash on Delivery")
        st.write("• Digital Wallets")

if __name__ == "__main__":
    main()
