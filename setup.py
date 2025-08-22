#!/usr/bin/env python3
"""
Setup script for Radhe Radhe & Sons Grocery Delivery Platform
"""

import os
import sys
import subprocess

def install_requirements():
    """Install required packages"""
    print("Installing required packages...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ All packages installed successfully!")
    except subprocess.CalledProcessError:
        print("❌ Error installing packages. Please install manually:")
        print("pip install -r requirements.txt")
        return False
    return True

def setup_database():
    """Initialize database and populate sample data"""
    print("\nSetting up database...")
    try:
        # Initialize database
        from database.models import init_database
        init_database()
        print("✅ Database tables created successfully!")
        
        # Populate sample data
        from database.sample_data import populate_sample_data
        populate_sample_data()
        print("✅ Sample data populated successfully!")
        
    except Exception as e:
        print(f"❌ Error setting up database: {e}")
        return False
    return True

def main():
    """Main setup function"""
    print("🛒 Setting up Radhe Radhe & Sons Grocery Delivery Platform")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not os.path.exists("main.py"):
        print("❌ Please run this script from the project root directory")
        return
    
    # Install requirements
    if not install_requirements():
        return
    
    # Setup database
    if not setup_database():
        return
    
    print("\n" + "=" * 60)
    print("🎉 Setup completed successfully!")
    print("\n📋 Demo Login Credentials:")
    print("👤 Admin User:")
    print("   Phone: 9754373333")
    print("   Password: admin123")
    print("\n👤 Demo Customer:")
    print("   Phone: 9999999999") 
    print("   Password: demo123")
    
    print("\n🚀 To run the application:")
    print("streamlit run main.py")
    
    print("\n📖 Features included:")
    print("✅ User Registration & Authentication")
    print("✅ Product Catalog with Search & Filters")
    print("✅ Shopping Cart & Checkout")
    print("✅ Order Management & Tracking")
    print("✅ Admin Dashboard")
    print("✅ Customer Profile & Address Management")
    print("✅ Loyalty Program")
    print("✅ Customer Support")
    print("✅ Responsive UI Design")

if __name__ == "__main__":
    main()
