const mongoose = require('mongoose');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');

const addressSchema = new mongoose.Schema({
  label: {
    type: String,
    required: true,
    enum: ['Home', 'Work', 'Other']
  },
  fullAddress: {
    type: String,
    required: true
  },
  landmark: String,
  pincode: {
    type: String,
    required: true,
    match: [/^[0-9]{6}$/, 'Please provide valid pincode']
  },
  coordinates: {
    latitude: {
      type: Number,
      required: true
    },
    longitude: {
      type: Number,
      required: true
    }
  },
  isDefault: {
    type: Boolean,
    default: false
  }
}, { _id: true });

const userSchema = new mongoose.Schema({
  name: {
    type: String,
    required: [true, 'Please provide name'],
    maxlength: [50, 'Name cannot exceed 50 characters']
  },
  email: {
    type: String,
    unique: true,
    sparse: true, // Allow multiple documents without email
    match: [
      /^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$/,
      'Please provide valid email'
    ]
  },
  phone: {
    type: String,
    required: [true, 'Please provide phone number'],
    unique: true,
    match: [/^[6-9]\d{9}$/, 'Please provide valid Indian mobile number']
  },
  password: {
    type: String,
    minlength: [6, 'Password must be at least 6 characters']
  },
  avatar: {
    public_id: String,
    url: String
  },
  addresses: [addressSchema],
  defaultAddress: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'addresses'
  },
  loyaltyPoints: {
    type: Number,
    default: 0
  },
  isEmailVerified: {
    type: Boolean,
    default: false
  },
  isPhoneVerified: {
    type: Boolean,
    default: false
  },
  role: {
    type: String,
    enum: ['user', 'admin', 'delivery_partner'],
    default: 'user'
  },
  status: {
    type: String,
    enum: ['active', 'inactive', 'blocked'],
    default: 'active'
  },
  lastLogin: Date,
  registrationSource: {
    type: String,
    enum: ['phone', 'email', 'google', 'facebook'],
    default: 'phone'
  },
  referralCode: {
    type: String,
    unique: true
  },
  referredBy: {
    type: String // referral code of the user who referred
  },
  preferences: {
    notifications: {
      email: { type: Boolean, default: true },
      sms: { type: Boolean, default: true },
      push: { type: Boolean, default: true }
    },
    language: { type: String, default: 'en' }
  },
  // OTP related fields
  otp: String,
  otpExpiry: Date,
  passwordResetToken: String,
  passwordResetExpire: Date
}, {
  timestamps: true
});

// Index for faster queries
userSchema.index({ phone: 1 });
userSchema.index({ email: 1 });
userSchema.index({ referralCode: 1 });

// Pre-save middleware to hash password
userSchema.pre('save', async function(next) {
  if (!this.isModified('password')) {
    next();
  }
  
  const salt = await bcrypt.genSalt(10);
  this.password = await bcrypt.hash(this.password, salt);
  next();
});

// Generate referral code before saving
userSchema.pre('save', function(next) {
  if (!this.referralCode) {
    this.referralCode = `RR${Math.random().toString(36).substring(2, 8).toUpperCase()}`;
  }
  next();
});

// Compare password method
userSchema.methods.matchPassword = async function(enteredPassword) {
  return await bcrypt.compare(enteredPassword, this.password);
};

// Generate JWT Token
userSchema.methods.getJWTToken = function() {
  return jwt.sign({ id: this._id }, process.env.JWT_SECRET, {
    expiresIn: process.env.JWT_EXPIRE || '7d'
  });
};

// Generate and hash OTP
userSchema.methods.generateOTP = function() {
  const otp = Math.floor(100000 + Math.random() * 900000).toString();
  
  this.otp = otp;
  this.otpExpiry = Date.now() + (process.env.OTP_EXPIRE_TIME || 5) * 60 * 1000; // 5 minutes
  
  return otp;
};

// Verify OTP
userSchema.methods.verifyOTP = function(enteredOTP) {
  return this.otp === enteredOTP && Date.now() <= this.otpExpiry;
};

// Clear OTP
userSchema.methods.clearOTP = function() {
  this.otp = undefined;
  this.otpExpiry = undefined;
};

// Add address method
userSchema.methods.addAddress = function(addressData) {
  // If this is the first address or marked as default, make it default
  if (this.addresses.length === 0 || addressData.isDefault) {
    // Remove default from other addresses
    this.addresses.forEach(addr => addr.isDefault = false);
    addressData.isDefault = true;
  }
  
  this.addresses.push(addressData);
  
  // Set as default address if it's the default
  if (addressData.isDefault) {
    this.defaultAddress = this.addresses[this.addresses.length - 1]._id;
  }
  
  return this.save();
};

// Update loyalty points
userSchema.methods.updateLoyaltyPoints = function(points) {
  this.loyaltyPoints += points;
  return this.save();
};

module.exports = mongoose.model('User', userSchema);
