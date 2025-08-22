const mongoose = require('mongoose');

const couponSchema = new mongoose.Schema({
  code: {
    type: String,
    required: [true, 'Coupon code is required'],
    unique: true,
    uppercase: true,
    trim: true,
    maxlength: [20, 'Coupon code cannot exceed 20 characters']
  },
  description: {
    type: String,
    required: [true, 'Coupon description is required'],
    maxlength: [200, 'Description cannot exceed 200 characters']
  },
  discountType: {
    type: String,
    enum: ['percentage', 'fixed'],
    required: true
  },
  discountValue: {
    type: Number,
    required: [true, 'Discount value is required'],
    min: [0, 'Discount value must be positive']
  },
  minOrderAmount: {
    type: Number,
    default: 0,
    min: [0, 'Minimum order amount must be positive']
  },
  maxDiscount: {
    type: Number, // Only for percentage coupons
    min: [0, 'Maximum discount must be positive']
  },
  usageLimit: {
    type: Number,
    default: null // null means unlimited usage
  },
  usedCount: {
    type: Number,
    default: 0
  },
  userUsageLimit: {
    type: Number,
    default: 1 // How many times a single user can use this coupon
  },
  validFrom: {
    type: Date,
    required: true
  },
  validUntil: {
    type: Date,
    required: true
  },
  applicableCategories: [{
    type: mongoose.Schema.Types.ObjectId,
    ref: 'Category'
  }],
  applicableProducts: [{
    type: mongoose.Schema.Types.ObjectId,
    ref: 'Product'
  }],
  excludeProducts: [{
    type: mongoose.Schema.Types.ObjectId,
    ref: 'Product'
  }],
  isActive: {
    type: Boolean,
    default: true
  },
  isFirstOrderOnly: {
    type: Boolean,
    default: false
  },
  isReferralReward: {
    type: Boolean,
    default: false
  },
  createdBy: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User',
    required: true
  }
}, {
  timestamps: true
});

// Indexes
couponSchema.index({ code: 1 });
couponSchema.index({ isActive: 1, validFrom: 1, validUntil: 1 });
couponSchema.index({ validUntil: 1 });

// Virtual to check if coupon is expired
couponSchema.virtual('isExpired').get(function() {
  return Date.now() > this.validUntil;
});

// Virtual to check if coupon is valid for usage
couponSchema.virtual('isValidForUsage').get(function() {
  return this.isActive && 
         Date.now() >= this.validFrom && 
         Date.now() <= this.validUntil &&
         (this.usageLimit === null || this.usedCount < this.usageLimit);
});

// Method to check if user can use this coupon
couponSchema.methods.canUserUseCoupon = async function(userId) {
  if (!this.isValidForUsage) {
    return { canUse: false, reason: 'Coupon is not valid' };
  }
  
  // Check if it's for first order only
  if (this.isFirstOrderOnly) {
    const Order = mongoose.model('Order');
    const orderCount = await Order.countDocuments({ 
      user: userId, 
      status: { $ne: 'cancelled' } 
    });
    
    if (orderCount > 0) {
      return { canUse: false, reason: 'This coupon is only valid for first order' };
    }
  }
  
  // Check user usage limit
  const CouponUsage = mongoose.model('CouponUsage');
  const userUsageCount = await CouponUsage.countDocuments({
    coupon: this._id,
    user: userId
  });
  
  if (userUsageCount >= this.userUsageLimit) {
    return { canUse: false, reason: 'You have already used this coupon maximum times' };
  }
  
  return { canUse: true };
};

// Method to calculate discount for cart
couponSchema.methods.calculateDiscount = function(cartTotal, cartItems = []) {
  if (!this.isValidForUsage) {
    throw new Error('Coupon is not valid');
  }
  
  if (cartTotal < this.minOrderAmount) {
    throw new Error(`Minimum order amount of ₹${this.minOrderAmount} required`);
  }
  
  // If specific categories or products are specified, check if cart items qualify
  let applicableAmount = cartTotal;
  
  if (this.applicableCategories.length > 0 || this.applicableProducts.length > 0) {
    // Calculate applicable amount based on category/product restrictions
    // This would need cart items with product/category details
    // For now, assuming full cart amount is applicable
  }
  
  let discount = 0;
  if (this.discountType === 'percentage') {
    discount = (applicableAmount * this.discountValue) / 100;
    if (this.maxDiscount) {
      discount = Math.min(discount, this.maxDiscount);
    }
  } else {
    discount = this.discountValue;
  }
  
  return Math.min(discount, applicableAmount);
};

// Method to use coupon (increment usage count)
couponSchema.methods.useCoupon = async function(userId) {
  this.usedCount += 1;
  await this.save();
  
  // Record usage
  const CouponUsage = mongoose.model('CouponUsage');
  await CouponUsage.create({
    coupon: this._id,
    user: userId,
    usedAt: new Date()
  });
};

// Static method to get valid coupons for user
couponSchema.statics.getValidCouponsForUser = async function(userId) {
  const now = new Date();
  
  return this.find({
    isActive: true,
    validFrom: { $lte: now },
    validUntil: { $gte: now },
    $or: [
      { usageLimit: null },
      { $expr: { $lt: ['$usedCount', '$usageLimit'] } }
    ]
  }).select('-createdBy');
};

module.exports = mongoose.model('Coupon', couponSchema);
