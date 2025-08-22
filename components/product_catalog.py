import streamlit as st
import pandas as pd
from database.operations import DatabaseOperations
from utils.auth import get_current_user, update_cart_count

def show_product_grid(products, columns=3):
    """Display products in a grid layout"""
    if not products:
        st.info("No products found")
        return
    
    # Create product grid
    cols = st.columns(columns)
    
    for idx, product in enumerate(products):
        col_idx = idx % columns
        
        with cols[col_idx]:
            # Product card
            with st.container():
                st.markdown(f"""
                <div style='border: 1px solid #ddd; border-radius: 10px; padding: 15px; margin: 10px 0; background: white; box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>
                    <div style='text-align: center;'>
                        <img src='{product.get('image_url', 'https://via.placeholder.com/150x100?text=No+Image')}' 
                             style='width: 100%; height: 120px; object-fit: cover; border-radius: 8px;' />
                    </div>
                    <h4 style='color: #2E7D32; margin: 10px 0 5px 0; font-size: 16px;'>{product['name']}</h4>
                    <p style='color: #666; font-size: 12px; margin: 5px 0;'>{product.get('description', '')[:50]}...</p>
                    <p style='color: #FF6B6B; font-size: 14px; margin: 5px 0;'><strong>₹{product['price']}/{product['unit']}</strong></p>
                    {f"<p style='color: #999; text-decoration: line-through; font-size: 12px;'>₹{product['original_price']}</p>" if product.get('original_price') and product['original_price'] > product['price'] else ""}
                    <p style='color: {"#4CAF50" if product["stock_quantity"] > 0 else "#F44336"}; font-size: 12px;'>
                        {"In Stock" if product["stock_quantity"] > 0 else "Out of Stock"}
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                # Add to cart controls
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    quantity = st.number_input(
                        f"Qty", 
                        min_value=1, 
                        max_value=min(10, product['stock_quantity']), 
                        value=1, 
                        key=f"qty_{product['product_id']}",
                        label_visibility="collapsed"
                    )
                
                with col2:
                    if st.button("🛒", key=f"add_{product['product_id']}", help="Add to cart", use_container_width=True):
                        user = get_current_user()
                        if user:
                            if DatabaseOperations.add_to_cart(user['user_id'], product['product_id'], quantity):
                                st.success(f"Added {quantity} {product['unit']} to cart!")
                                update_cart_count()
                                st.rerun()
                            else:
                                st.error("Failed to add to cart")
                        else:
                            st.warning("Please login to add items to cart")

def show_category_filter():
    """Show category filter sidebar"""
    st.sidebar.subheader("🗂️ Categories")
    
    categories = DatabaseOperations.get_categories()
    category_options = ["All Categories"] + [cat['name'] for cat in categories]
    
    selected_category = st.sidebar.selectbox(
        "Filter by Category", 
        category_options,
        key="category_filter"
    )
    
    if selected_category == "All Categories":
        return None
    else:
        # Find category ID
        for cat in categories:
            if cat['name'] == selected_category:
                return cat['id']
    return None

def show_search_bar():
    """Show search functionality"""
    col1, col2 = st.columns([4, 1])
    
    with col1:
        search_query = st.text_input(
            "🔍 Search products", 
            placeholder="Search for fruits, vegetables, snacks...",
            key="product_search"
        )
    
    with col2:
        search_button = st.button("Search", use_container_width=True)
    
    return search_query if search_query or search_button else None

def show_price_filter():
    """Show price range filter"""
    st.sidebar.subheader("💰 Price Range")
    
    price_range = st.sidebar.slider(
        "Select price range",
        min_value=0,
        max_value=1000,
        value=(0, 1000),
        step=10,
        key="price_filter"
    )
    
    return price_range

def filter_products_by_price(products, price_range):
    """Filter products by price range"""
    min_price, max_price = price_range
    return [
        product for product in products
        if min_price <= product['price'] <= max_price
    ]

def show_sort_options():
    """Show sorting options"""
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.subheader("🛒 Products")
    
    with col2:
        sort_option = st.selectbox(
            "Sort by",
            ["Name A-Z", "Name Z-A", "Price Low-High", "Price High-Low", "Newest First"],
            key="sort_products"
        )
    
    return sort_option

def sort_products(products, sort_option):
    """Sort products based on selected option"""
    if sort_option == "Name A-Z":
        return sorted(products, key=lambda x: x['name'].lower())
    elif sort_option == "Name Z-A":
        return sorted(products, key=lambda x: x['name'].lower(), reverse=True)
    elif sort_option == "Price Low-High":
        return sorted(products, key=lambda x: x['price'])
    elif sort_option == "Price High-Low":
        return sorted(products, key=lambda x: x['price'], reverse=True)
    else:  # Newest First
        return products  # Already sorted by creation date in DB

def show_product_catalog():
    """Main product catalog page"""
    st.title("🛍️ Product Catalog")
    
    # Filters and search
    category_id = show_category_filter()
    price_range = show_price_filter()
    search_query = show_search_bar()
    sort_option = show_sort_options()
    
    # Get products
    products = DatabaseOperations.get_products(
        category_id=category_id,
        search_query=search_query
    )
    
    # Apply price filter
    if price_range:
        products = filter_products_by_price(products, price_range)
    
    # Apply sorting
    products = sort_products(products, sort_option)
    
    # Show results count
    st.write(f"Found {len(products)} products")
    
    # Display products
    if products:
        show_product_grid(products)
    else:
        st.info("No products match your filters. Try adjusting your search criteria.")

def show_category_showcase():
    """Show featured categories on home page"""
    st.subheader("🗂️ Shop by Category")
    
    categories = DatabaseOperations.get_categories()
    
    if categories:
        # Display categories in a grid
        cols = st.columns(min(4, len(categories)))
        
        for idx, category in enumerate(categories):
            col_idx = idx % len(cols)
            
            with cols[col_idx]:
                st.markdown(f"""
                <div style='text-align: center; padding: 20px; border: 1px solid #ddd; 
                           border-radius: 10px; margin: 10px 0; cursor: pointer; 
                           background: linear-gradient(135deg, #E8F5E8, #C8E6C9);'>
                    <h3 style='color: #2E7D32; margin: 10px 0;'>{category['name']}</h3>
                    <p style='color: #666; font-size: 12px;'>{category.get('description', '')}</p>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button(f"Browse {category['name']}", key=f"cat_{category['id']}", use_container_width=True):
                    st.session_state.current_page = 'products'
                    st.session_state.selected_category = category['id']
                    st.rerun()

def show_featured_products():
    """Show featured products on home page"""
    st.subheader("⭐ Featured Products")
    
    # Get some random featured products (limit 6)
    products = DatabaseOperations.get_products(limit=6)
    
    if products:
        show_product_grid(products, columns=3)
    else:
        st.info("No featured products available")

def show_product_details(product_id):
    """Show detailed product view"""
    product = DatabaseOperations.get_product_by_id(product_id)
    
    if not product:
        st.error("Product not found")
        return
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.image(
            product.get('image_url', 'https://via.placeholder.com/300x200?text=No+Image'),
            use_column_width=True
        )
    
    with col2:
        st.subheader(product['name'])
        st.write(f"**Category:** {product.get('category_name', 'N/A')}")
        st.write(f"**Description:** {product.get('description', 'No description available')}")
        
        # Price display
        col_price1, col_price2 = st.columns(2)
        with col_price1:
            st.markdown(f"**Price:** ₹{product['price']}/{product['unit']}")
        with col_price2:
            if product.get('original_price') and product['original_price'] > product['price']:
                discount = round((1 - product['price']/product['original_price']) * 100)
                st.markdown(f"~~₹{product['original_price']}~~ **({discount}% off)**")
        
        # Stock status
        if product['stock_quantity'] > 0:
            st.success(f"✅ In Stock ({product['stock_quantity']} available)")
        else:
            st.error("❌ Out of Stock")
        
        # Add to cart
        if product['stock_quantity'] > 0:
            quantity = st.number_input(
                "Quantity", 
                min_value=1, 
                max_value=min(10, product['stock_quantity']), 
                value=1
            )
            
            if st.button("🛒 Add to Cart", use_container_width=True):
                user = get_current_user()
                if user:
                    if DatabaseOperations.add_to_cart(user['user_id'], product['product_id'], quantity):
                        st.success(f"Added {quantity} {product['unit']} to cart!")
                        update_cart_count()
                        st.rerun()
                    else:
                        st.error("Failed to add to cart")
                else:
                    st.warning("Please login to add items to cart")
