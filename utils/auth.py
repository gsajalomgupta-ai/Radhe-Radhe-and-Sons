import streamlit as st
import re
from database.operations import DatabaseOperations

def is_valid_phone(phone):
    """Validate Indian phone number format"""
    pattern = r'^[6-9]\d{9}$'
    return bool(re.match(pattern, phone))

def is_valid_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def init_session_state():
    """Initialize session state variables"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'cart_count' not in st.session_state:
        st.session_state.cart_count = 0
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'home'

def login_user(user_data):
    """Login user and update session state"""
    st.session_state.authenticated = True
    st.session_state.user = user_data
    update_cart_count()

def logout_user():
    """Logout user and clear session state"""
    st.session_state.authenticated = False
    st.session_state.user = None
    st.session_state.cart_count = 0

def get_current_user():
    """Get current logged in user"""
    return st.session_state.user if st.session_state.authenticated else None

def is_admin():
    """Check if current user is admin"""
    user = get_current_user()
    return user and user.get('is_admin', False)

def update_cart_count():
    """Update cart count in session state"""
    user = get_current_user()
    if user:
        cart_items = DatabaseOperations.get_cart_items(user['user_id'])
        st.session_state.cart_count = sum(item['quantity'] for item in cart_items)
    else:
        st.session_state.cart_count = 0

def show_login_form():
    """Display login form"""
    st.subheader("🔐 Login to Radhe Radhe & Sons")
    
    with st.form("login_form"):
        phone = st.text_input("Phone Number", placeholder="Enter 10-digit mobile number")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        submitted = st.form_submit_button("Login", use_container_width=True)
        
        if submitted:
            if not phone or not password:
                st.error("Please fill all fields")
                return False
            
            if not is_valid_phone(phone):
                st.error("Please enter valid 10-digit phone number")
                return False
            
            user = DatabaseOperations.authenticate_user(phone, password)
            if user:
                login_user(user)
                st.success(f"Welcome back, {user['name']}!")
                st.rerun()
                return True
            else:
                st.error("Invalid phone number or password")
                return False
    
    return False

def show_registration_form():
    """Display registration form"""
    st.subheader("📝 Register with Radhe Radhe & Sons")
    
    with st.form("register_form"):
        name = st.text_input("Full Name", placeholder="Enter your full name")
        phone = st.text_input("Phone Number", placeholder="Enter 10-digit mobile number")
        email = st.text_input("Email (Optional)", placeholder="Enter your email address")
        password = st.text_input("Password", type="password", placeholder="Create a password")
        confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm your password")
        
        col1, col2 = st.columns(2)
        with col1:
            send_otp = st.form_submit_button("Send OTP", use_container_width=True)
        with col2:
            register = st.form_submit_button("Register", use_container_width=True)
        
        if send_otp:
            if not phone:
                st.error("Please enter phone number")
                return False
            
            if not is_valid_phone(phone):
                st.error("Please enter valid 10-digit phone number")
                return False
            
            otp = DatabaseOperations.generate_otp(phone)
            st.success(f"OTP sent to {phone}: **{otp}** (Demo OTP)")
            st.session_state.otp_sent = True
            st.session_state.registration_phone = phone
            return False
        
        if register:
            if not all([name, phone, password, confirm_password]):
                st.error("Please fill all required fields")
                return False
            
            if not is_valid_phone(phone):
                st.error("Please enter valid 10-digit phone number")
                return False
            
            if email and not is_valid_email(email):
                st.error("Please enter valid email address")
                return False
            
            if password != confirm_password:
                st.error("Passwords do not match")
                return False
            
            if len(password) < 6:
                st.error("Password must be at least 6 characters long")
                return False
            
            # For demo, skip OTP verification
            user_id = DatabaseOperations.create_user(name, phone, email, password)
            if user_id:
                st.success("Registration successful! Please login.")
                return True
            else:
                st.error("Registration failed. Phone number might already exist.")
                return False
    
    return False

def show_otp_verification_form():
    """Display OTP verification form"""
    if 'otp_sent' not in st.session_state:
        return False
    
    st.subheader("🔐 Verify OTP")
    
    with st.form("otp_form"):
        otp = st.text_input("Enter OTP", placeholder="Enter 6-digit OTP")
        verify = st.form_submit_button("Verify OTP", use_container_width=True)
        
        if verify:
            if not otp:
                st.error("Please enter OTP")
                return False
            
            phone = st.session_state.get('registration_phone', '')
            if DatabaseOperations.verify_otp(phone, otp):
                st.success("OTP verified successfully!")
                del st.session_state.otp_sent
                del st.session_state.registration_phone
                return True
            else:
                st.error("Invalid or expired OTP")
                return False
    
    return False

def require_auth(admin_required=False):
    """Decorator to require authentication"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            if not st.session_state.authenticated:
                st.warning("Please login to access this page")
                show_auth_page()
                return None
            
            if admin_required and not is_admin():
                st.error("Admin access required")
                return None
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

def show_auth_page():
    """Show authentication page with login/register tabs"""
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        show_login_form()
    
    with tab2:
        if 'otp_sent' in st.session_state:
            show_otp_verification_form()
        else:
            show_registration_form()
