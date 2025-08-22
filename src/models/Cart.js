const mongoose = require('mongoose');

const cartItemSchema = new mongoose.Schema({
  product: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'Product',
    required: true
  },
  variant: {
    type: mongoose.Schema.Types.ObjectId,
    required: true
  },
  quantity: {
    type: Number,
    required: true,
    min: 1
  },
  price: {
    mrp: Number,
    sellingPrice: Number,
    discount: Number
  },
  addedAt: {
    type: Date,
    default: Date.now
  }
});

const cartSchema = new mongoose.Schema({
  user: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User',
    required: true,
    unique: true
  },
  items: [cartItemSchema],
  couponCode: String,
  couponDiscount: {
    type: Number,
    default: 0
  },
  totalItems: {
    type: Number,
    default: 0
  },
  subtotal: {
    type: Number,
    default: 0
  },
  totalDiscount: {
    type: Number,
    default: 0
  },
  deliveryCharge: {
    type: Number,
    default: 0
  },
  totalAmount: {
    type: Number,
    default: 0
  },
  lastUpdated: {
    type: Date,
    default: Date.now
  }
}, {
  timestamps: true
});

// Index for faster queries
cartSchema.index({ user: 1 });
cartSchema.index({ 'items.product': 1 });

// Pre-save middleware to calculate totals
cartSchema.pre('save', function(next) {
  this.totalItems = this.items.reduce((total, item) => total + item.quantity, 0);
  this.subtotal = this.items.reduce((total, item) => total + (item.price.sellingPrice * item.quantity), 0);
  this.totalDiscount = this.items.reduce((total, item) => {
    const itemDiscount = (item.price.mrp - item.price.sellingPrice) * item.quantity;
    return total + itemDiscount;
  }, 0) + this.couponDiscount;
  
  // Calculate delivery charge
  const minOrderAmount = process.env.MIN_ORDER_AMOUNT || 99;
  const deliveryCharge = process.env.DELIVERY_CHARGE || 29;
  const freeDeliveryAbove = process.env.FREE_DELIVERY_ABOVE || 299;
  
  if (this.subtotal >= freeDeliveryAbove) {
    this.deliveryCharge = 0;
  } else if (this.subtotal >= minOrderAmount) {
    this.deliveryCharge = deliveryCharge;
  } else {
    this.deliveryCharge = 0; // No delivery for orders below minimum
  }
  
  this.totalAmount = this.subtotal + this.deliveryCharge - this.couponDiscount;
  this.lastUpdated = Date.now();
  
  next();
});

// Method to add item to cart
cartSchema.methods.addItem = async function(productId, variantId, quantity = 1) {
  const Product = mongoose.model('Product');
  const product = await Product.findById(productId);
  
  if (!product) {
    throw new Error('Product not found');
  }
  
  const variant = product.variants.id(variantId);
  if (!variant) {
    throw new Error('Product variant not found');
  }
  
  if (!product.isAvailable(variantId, quantity)) {
    throw new Error('Insufficient stock');
  }
  
  // Check if item already exists in cart
  const existingItemIndex = this.items.findIndex(
    item => item.product.toString() === productId && item.variant.toString() === variantId
  );
  
  if (existingItemIndex > -1) {
    // Update quantity of existing item
    const newQuantity = this.items[existingItemIndex].quantity + quantity;
    
    if (!product.isAvailable(variantId, newQuantity)) {
      throw new Error('Insufficient stock for requested quantity');
    }
    
    this.items[existingItemIndex].quantity = newQuantity;
  } else {
    // Add new item
    this.items.push({
      product: productId,
      variant: variantId,
      quantity: quantity,
      price: {
        mrp: variant.price.mrp,
        sellingPrice: variant.price.sellingPrice,
        discount: variant.price.discount
      }
    });
  }
  
  return this.save();
};

// Method to update item quantity
cartSchema.methods.updateItemQuantity = async function(productId, variantId, quantity) {
  const Product = mongoose.model('Product');
  const product = await Product.findById(productId);
  
  if (!product) {
    throw new Error('Product not found');
  }
  
  if (!product.isAvailable(variantId, quantity)) {
    throw new Error('Insufficient stock');
  }
  
  const itemIndex = this.items.findIndex(
    item => item.product.toString() === productId && item.variant.toString() === variantId
  );
  
  if (itemIndex === -1) {
    throw new Error('Item not found in cart');
  }
  
  if (quantity <= 0) {
    this.items.splice(itemIndex, 1);
  } else {
    this.items[itemIndex].quantity = quantity;
  }
  
  return this.save();
};

// Method to remove item from cart
cartSchema.methods.removeItem = function(productId, variantId) {
  this.items = this.items.filter(
    item => !(item.product.toString() === productId && item.variant.toString() === variantId)
  );
  
  return this.save();
};

// Method to clear cart
cartSchema.methods.clearCart = function() {
  this.items = [];
  this.couponCode = undefined;
  this.couponDiscount = 0;
  
  return this.save();
};

// Method to apply coupon
cartSchema.methods.applyCoupon = async function(couponCode) {
  const Coupon = mongoose.model('Coupon');
  const coupon = await Coupon.findOne({ 
    code: couponCode, 
    isActive: true,
    validFrom: { $lte: new Date() },
    validUntil: { $gte: new Date() }
  });
  
  if (!coupon) {
    throw new Error('Invalid or expired coupon');
  }
  
  if (this.subtotal < coupon.minOrderAmount) {
    throw new Error(`Minimum order amount of ₹${coupon.minOrderAmount} required`);
  }
  
  let discount = 0;
  if (coupon.discountType === 'percentage') {
    discount = (this.subtotal * coupon.discountValue) / 100;
    if (coupon.maxDiscount) {
      discount = Math.min(discount, coupon.maxDiscount);
    }
  } else {
    discount = coupon.discountValue;
  }
  
  this.couponCode = couponCode;
  this.couponDiscount = discount;
  
  return this.save();
};

// Method to remove coupon
cartSchema.methods.removeCoupon = function() {
  this.couponCode = undefined;
  this.couponDiscount = 0;
  
  return this.save();
};

// Static method to get or create cart
cartSchema.statics.getCartByUser = async function(userId) {
  let cart = await this.findOne({ user: userId }).populate('items.product');
  
  if (!cart) {
    cart = await this.create({ user: userId });
  }
  
  return cart;
};

module.exports = mongoose.model('Cart', cartSchema);
