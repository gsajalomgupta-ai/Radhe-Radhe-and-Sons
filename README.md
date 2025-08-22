# 🛒 Radhe Radhe & Sons - Grocery Delivery Platform

A comprehensive **Quick-Commerce Grocery Delivery Platform** built with **Python & Streamlit** for **Prakhar Gupta's** grocery business.

## 📱 Contact Information
- **Owner:** Prakhar Gupta
- **Phone:** +91 9754373333
- **Business:** Fresh Groceries & Daily Needs Delivery

## 🌟 Features Overview

### 🔐 User Management
- Phone/Email/Social Media Registration & Login
- OTP-based secure authentication
- Profile management with delivery addresses
- Order history and 1-click reordering
- Loyalty points system

### 🛍️ Product Catalog
- Browse by categories (Fruits, Vegetables, Dairy, Snacks, etc.)
- Advanced search with filters (price, brand, category)
- Real-time stock availability
- Product favorites/wishlist
- Detailed product information with images

### 🛒 Shopping Cart & Checkout
- Add/remove items with quantity management
- Real-time price calculation
- Discount coupons & promo codes
- Multiple payment options (UPI, Cards, COD, Wallets)
- Secure payment processing

### 📦 Order Management
- Real-time order tracking (Pending → Packed → Out for Delivery → Delivered)
- SMS/Push/Email notifications
- Order cancellation (before packing)
- Refund/return request handling
- Delivery time estimation

### 🚚 Delivery Management
- 5km delivery radius restriction
- Real-time delivery partner assignment
- Live GPS tracking simulation
- Estimated Delivery Time (EDT)
- Delivery confirmation system

### 🔧 Admin Dashboard
- Product & inventory management
- Order processing & status updates
- Customer management
- Sales analytics & reports
- System configuration

### 🏆 Customer Features
- Multiple delivery addresses
- Loyalty points & rewards
- Personalized recommendations
- Referral program
- Customer support system

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Installation

1. **Clone or download the project**
   ```bash
   # Navigate to the project directory
   cd "Radhe Radhe and Sons"
   ```

2. **Run the setup script**
   ```bash
   python setup.py
   ```

3. **Start the application**
   ```bash
   streamlit run main.py
   ```

4. **Access the application**
   - Open your browser and go to `http://localhost:8501`

## 🔑 Demo Login Credentials

### Admin Access
- **Phone:** 9754373333
- **Password:** admin123

### Customer Access  
- **Phone:** 9999999999
- **Password:** demo123

## 📂 Project Structure

```
Radhe Radhe and Sons/
├── main.py                 # Main Streamlit application
├── setup.py               # Setup script
├── requirements.txt       # Python dependencies
├── README.md             # Project documentation
│
├── database/
│   ├── models.py         # Database schema & models
│   ├── operations.py     # Database CRUD operations
│   └── sample_data.py    # Sample data population
│
├── utils/
│   └── auth.py          # Authentication utilities
│
├── components/
│   ├── product_catalog.py    # Product browsing & search
│   ├── cart_checkout.py      # Shopping cart & checkout
│   ├── order_management.py   # Order tracking & history
│   ├── admin_dashboard.py    # Admin management panel
│   └── customer_features.py # Customer profile & features
│
├── pages/               # Additional Streamlit pages
├── assets/             # Static assets (images, etc.)
└── database/           # SQLite database storage
```

## 🛡️ Security Features

- **Password Hashing:** SHA-256 encryption
- **OTP Authentication:** 6-digit OTP verification
- **Session Management:** Secure session handling
- **Input Validation:** Phone/email format validation
- **Data Privacy:** GDPR compliant data handling

## 💳 Payment Methods Supported

- **UPI:** PhonePe, Google Pay, Paytm
- **Cards:** Debit/Credit cards
- **Net Banking:** All major banks
- **Cash on Delivery:** Available
- **Digital Wallets:** Multiple wallet support

## 🎯 Business Logic

### Pricing & Delivery
- **Free Delivery:** Orders above ₹500
- **Delivery Charges:** ₹30 for orders below ₹500
- **Delivery Time:** 30-90 minutes
- **Service Area:** 5km radius from store

### Loyalty Program
- **Earn:** 1 point per ₹10 spent
- **Redeem:** 100 points = ₹10 discount
- **Tiers:** Bronze, Silver, Gold based on points

### Discount Coupons
- **WELCOME10:** 10% off on orders above ₹200
- **FLAT50:** ₹50 off on orders above ₹300
- **FIRST20:** 20% off for new customers (min ₹150)

## 📊 Admin Features

### Dashboard Analytics
- Daily/Weekly/Monthly sales reports
- Revenue tracking & trends
- Order status distribution
- Top-selling products analysis
- Customer analytics

### Inventory Management
- Real-time stock tracking
- Low stock alerts
- Product addition/modification
- Category management
- Price management

### Order Management
- Order processing workflow
- Status updates (Pending → Delivered)
- Customer communication
- Delivery assignment
- Return/refund processing

## 🛠️ Technical Specifications

### Frontend
- **Framework:** Streamlit
- **UI Components:** Native Streamlit widgets
- **Styling:** Custom CSS with gradient themes
- **Responsive:** Mobile-friendly design

### Backend
- **Language:** Python 3.8+
- **Database:** SQLite (easily upgradeable to PostgreSQL)
- **Authentication:** Session-based with OTP
- **File Structure:** Modular component architecture

### Database Schema
- **Users:** Authentication & profile data
- **Products:** Inventory & catalog information
- **Orders:** Transaction & fulfillment data
- **Categories:** Product organization
- **Addresses:** Delivery locations
- **Coupons:** Promotional offers

## 🔄 Order Workflow

1. **Order Placement:** Customer places order
2. **Payment Processing:** Secure payment handling
3. **Order Confirmation:** Automatic confirmation
4. **Preparation:** Items packed for delivery
5. **Dispatch:** Assigned to delivery partner
6. **Delivery:** Real-time tracking available
7. **Completion:** Delivery confirmation & feedback

## 📱 Customer Support

### Contact Methods
- **Phone:** +91 9754373333
- **Email:** support@radheradheandsons.com
- **In-App:** Customer support chat
- **Hours:** 9 AM - 9 PM (All days)

### Support Features
- FAQ section with common queries
- Order issue reporting
- Live chat support (simulated)
- Feedback & rating system

## 🎨 UI/UX Features

### Design Theme
- **Colors:** Green gradient theme (representing freshness)
- **Icons:** Emoji-based intuitive navigation
- **Layout:** Clean, spacious design
- **Typography:** Clear, readable fonts

### User Experience
- **Navigation:** Simple, intuitive menu structure
- **Search:** Powerful search with auto-suggestions
- **Filters:** Easy-to-use filtering options
- **Feedback:** Real-time success/error messages

## 📈 Scalability Considerations

### Performance
- **Database:** SQLite for development, easily upgradeable
- **Caching:** Session state management
- **Optimization:** Efficient query structures

### Future Enhancements
- **Real-time Notifications:** Push notification integration
- **GPS Tracking:** Actual GPS tracking implementation  
- **Payment Gateway:** Real payment processor integration
- **Mobile App:** React Native/Flutter mobile app
- **Multi-vendor:** Support for multiple suppliers

## 🧪 Testing

The application includes comprehensive sample data:
- **25+ Products** across 6 categories
- **Sample Users** with different roles
- **Demo Orders** for testing workflows
- **Address Management** examples
- **Coupon Codes** for testing discounts

## 🤝 Contributing

This is a demo project for **Radhe Radhe & Sons**. For business inquiries or technical improvements, contact:
- **Prakhar Gupta:** +91 9754373333

## 📄 License

This project is developed specifically for Radhe Radhe & Sons grocery business. All rights reserved.

## 🙏 Acknowledgments

- Built with ❤️ using **Streamlit**
- Sample images from **Unsplash**
- Icons and emojis for enhanced UX
- Modern web design principles

---

**Made with 💚 for Fresh Grocery Delivery**

*Radhe Radhe & Sons - Your Trusted Grocery Partner*
