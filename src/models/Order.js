const mongoose = require('mongoose');

const orderItemSchema = new mongoose.Schema({
  product: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'Product',
    required: true
  },
  variant: {
    type: mongoose.Schema.Types.ObjectId,
    required: true
  },
  productName: String, // Store product name for historical records
  variantDetails: {
    size: String,
    unit: String,
    quantity: Number
  },
  quantity: {
    type: Number,
    required: true,
    min: 1
  },
  price: {
    mrp: {
      type: Number,
      required: true
    },
    sellingPrice: {
      type: Number,
      required: true
    },
    discount: Number
  },
  totalPrice: {
    type: Number,
    required: true
  }
});

const deliveryAddressSchema = new mongoose.Schema({
  label: String,
  fullAddress: {
    type: String,
    required: true
  },
  landmark: String,
  pincode: {
    type: String,
    required: true
  },
  coordinates: {
    latitude: Number,
    longitude: Number
  }
});

const orderTrackingSchema = new mongoose.Schema({
  status: {
    type: String,
    required: true,
    enum: ['pending', 'confirmed', 'packed', 'out_for_delivery', 'delivered', 'cancelled', 'returned']
  },
  timestamp: {
    type: Date,
    default: Date.now
  },
  note: String,
  updatedBy: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User'
  }
});

const paymentDetailsSchema = new mongoose.Schema({
  method: {
    type: String,
    enum: ['cod', 'online', 'wallet', 'card', 'upi'],
    required: true
  },
  transactionId: String,
  razorpayOrderId: String,
  razorpayPaymentId: String,
  status: {
    type: String,
    enum: ['pending', 'completed', 'failed', 'refunded'],
    default: 'pending'
  },
  paidAmount: Number,
  refundId: String,
  refundAmount: Number,
  refundReason: String
});

const orderSchema = new mongoose.Schema({
  orderNumber: {
    type: String,
    unique: true,
    required: true
  },
  user: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User',
    required: true
  },
  items: {
    type: [orderItemSchema],
    validate: {
      validator: function(items) {
        return items.length > 0;
      },
      message: 'Order must have at least one item'
    }
  },
  orderSummary: {
    itemsCount: {
      type: Number,
      required: true
    },
    subtotal: {
      type: Number,
      required: true
    },
    discount: {
      type: Number,
      default: 0
    },
    couponDiscount: {
      type: Number,
      default: 0
    },
    deliveryCharge: {
      type: Number,
      default: 0
    },
    totalAmount: {
      type: Number,
      required: true
    }
  },
  couponCode: String,
  deliveryAddress: {
    type: deliveryAddressSchema,
    required: true
  },
  contactNumber: {
    type: String,
    required: true
  },
  status: {
    type: String,
    enum: ['pending', 'confirmed', 'packed', 'out_for_delivery', 'delivered', 'cancelled', 'returned'],
    default: 'pending'
  },
  tracking: [orderTrackingSchema],
  paymentDetails: paymentDetailsSchema,
  deliveryPartner: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User'
  },
  estimatedDeliveryTime: Date,
  actualDeliveryTime: Date,
  deliveryOTP: String,
  cancellationReason: String,
  returnReason: String,
  notes: String,
  loyaltyPointsEarned: {
    type: Number,
    default: 0
  },
  loyaltyPointsUsed: {
    type: Number,
    default: 0
  }
}, {
  timestamps: true
});

// Indexes for better performance
orderSchema.index({ orderNumber: 1 });
orderSchema.index({ user: 1, createdAt: -1 });
orderSchema.index({ status: 1 });
orderSchema.index({ deliveryPartner: 1 });
orderSchema.index({ createdAt: -1 });

// Pre-save middleware to generate order number and set initial tracking
orderSchema.pre('save', function(next) {
  if (this.isNew) {
    // Generate order number
    const timestamp = Date.now().toString().slice(-8);
    const random = Math.floor(Math.random() * 1000).toString().padStart(3, '0');
    this.orderNumber = `RR${timestamp}${random}`;
    
    // Set initial tracking
    this.tracking.push({
      status: this.status,
      timestamp: new Date(),
      note: 'Order placed successfully'
    });
    
    // Generate delivery OTP for cash on delivery
    if (this.paymentDetails.method === 'cod') {
      this.deliveryOTP = Math.floor(1000 + Math.random() * 9000).toString();
    }
    
    // Set estimated delivery time (30 minutes from now)
    this.estimatedDeliveryTime = new Date(Date.now() + 30 * 60 * 1000);
    
    // Calculate loyalty points earned (1 point per ₹10)
    this.loyaltyPointsEarned = Math.floor(this.orderSummary.totalAmount / 10);
  }
  
  next();
});

// Method to update order status
orderSchema.methods.updateStatus = function(newStatus, note = '', updatedBy = null) {
  if (this.status === newStatus) {
    return Promise.resolve(this);
  }
  
  // Validate status transition
  const validTransitions = {
    'pending': ['confirmed', 'cancelled'],
    'confirmed': ['packed', 'cancelled'],
    'packed': ['out_for_delivery', 'cancelled'],
    'out_for_delivery': ['delivered', 'cancelled'],
    'delivered': ['returned'],
    'cancelled': [],
    'returned': []
  };
  
  if (!validTransitions[this.status].includes(newStatus)) {
    throw new Error(`Cannot change status from ${this.status} to ${newStatus}`);
  }
  
  this.status = newStatus;
  this.tracking.push({
    status: newStatus,
    timestamp: new Date(),
    note: note || this.getStatusMessage(newStatus),
    updatedBy
  });
  
  // Set delivery time for delivered orders
  if (newStatus === 'delivered') {
    this.actualDeliveryTime = new Date();
  }
  
  return this.save();
};

// Method to get status message
orderSchema.methods.getStatusMessage = function(status) {
  const messages = {
    'pending': 'Order is being processed',
    'confirmed': 'Order confirmed and being prepared',
    'packed': 'Order packed and ready for delivery',
    'out_for_delivery': 'Order is out for delivery',
    'delivered': 'Order delivered successfully',
    'cancelled': 'Order cancelled',
    'returned': 'Order returned'
  };
  
  return messages[status] || 'Status updated';
};

// Method to calculate refund amount
orderSchema.methods.calculateRefundAmount = function() {
  if (this.paymentDetails.method === 'cod') {
    return 0; // No refund for COD orders
  }
  
  // Full refund if cancelled before packing
  if (['pending', 'confirmed'].includes(this.status)) {
    return this.orderSummary.totalAmount;
  }
  
  // Partial refund (excluding delivery charge) if cancelled after packing
  if (this.status === 'packed') {
    return this.orderSummary.totalAmount - this.orderSummary.deliveryCharge;
  }
  
  // No refund if out for delivery or delivered
  return 0;
};

// Method to assign delivery partner
orderSchema.methods.assignDeliveryPartner = function(partnerId) {
  this.deliveryPartner = partnerId;
  return this.updateStatus('out_for_delivery', `Assigned to delivery partner`, partnerId);
};

// Static method to get orders by status
orderSchema.statics.getOrdersByStatus = function(status, page = 1, limit = 20) {
  return this.find({ status })
    .populate('user', 'name phone')
    .populate('deliveryPartner', 'name phone')
    .sort({ createdAt: -1 })
    .limit(limit * 1)
    .skip((page - 1) * limit);
};

// Static method to get user orders
orderSchema.statics.getUserOrders = function(userId, page = 1, limit = 10) {
  return this.find({ user: userId })
    .sort({ createdAt: -1 })
    .limit(limit * 1)
    .skip((page - 1) * limit);
};

// Static method to get delivery partner orders
orderSchema.statics.getDeliveryPartnerOrders = function(partnerId, status = null) {
  const query = { deliveryPartner: partnerId };
  if (status) {
    query.status = status;
  }
  
  return this.find(query)
    .populate('user', 'name phone')
    .sort({ createdAt: -1 });
};

// Virtual for order age in hours
orderSchema.virtual('orderAge').get(function() {
  return Math.floor((Date.now() - this.createdAt) / (1000 * 60 * 60));
});

// Virtual for delivery delay
orderSchema.virtual('isDelayed').get(function() {
  if (this.status === 'delivered' || this.status === 'cancelled') {
    return false;
  }
  return Date.now() > this.estimatedDeliveryTime;
});

module.exports = mongoose.model('Order', orderSchema);
