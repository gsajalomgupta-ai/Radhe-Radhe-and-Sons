const User = require('../models/User');
const smsService = require('../services/smsService');
const { body, validationResult } = require('express-validator');

// Send OTP for login/registration
const sendOTP = async (req, res, next) => {
  try {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({
        success: false,
        message: 'Validation error',
        errors: errors.array()
      });
    }

    const { phone } = req.body;

    // Check if user exists
    let user = await User.findOne({ phone });
    
    if (!user) {
      // Create new user with phone number
      user = new User({ 
        phone, 
        name: `User${phone.slice(-4)}` // Temporary name
      });
    }

    // Generate and save OTP
    const otp = user.generateOTP();
    await user.save({ validateBeforeSave: false });

    // Send OTP via SMS
    const smsResult = await smsService.sendOTP(phone, otp);
    
    if (!smsResult.success) {
      return res.status(500).json({
        success: false,
        message: 'Failed to send OTP. Please try again.'
      });
    }

    res.status(200).json({
      success: true,
      message: 'OTP sent successfully to your phone',
      data: {
        phone,
        otpSent: true,
        // Don't send actual OTP in production
        ...(process.env.NODE_ENV === 'development' && { otp })
      }
    });

  } catch (error) {
    next(error);
  }
};

// Verify OTP and login/register user
const verifyOTP = async (req, res, next) => {
  try {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({
        success: false,
        message: 'Validation error',
        errors: errors.array()
      });
    }

    const { phone, otp, name, referredBy } = req.body;

    const user = await User.findOne({ phone });
    
    if (!user) {
      return res.status(400).json({
        success: false,
        message: 'User not found. Please send OTP first.'
      });
    }

    // Verify OTP
    if (!user.verifyOTP(otp)) {
      return res.status(400).json({
        success: false,
        message: 'Invalid or expired OTP'
      });
    }

    // Check if it's a new user (first time verification)
    const isNewUser = !user.isPhoneVerified;

    // Update user details for new users
    if (isNewUser) {
      if (name) user.name = name;
      if (referredBy) {
        // Find referring user and add bonus points
        const referringUser = await User.findOne({ referralCode: referredBy });
        if (referringUser) {
          user.referredBy = referredBy;
          referringUser.loyaltyPoints += 50; // Referral bonus
          await referringUser.save();
        }
      }
    }

    // Mark phone as verified and clear OTP
    user.isPhoneVerified = true;
    user.status = 'active';
    user.clearOTP();
    
    await user.save();

    // Generate JWT token
    const token = user.getJWTToken();

    // Send welcome SMS for new users
    if (isNewUser) {
      await smsService.sendWelcomeMessage(phone, user.name, user.referralCode);
    }

    // Set cookie
    const cookieOptions = {
      expires: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000), // 7 days
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production'
    };

    res.status(200).cookie('token', token, cookieOptions).json({
      success: true,
      message: isNewUser ? 'Registration successful' : 'Login successful',
      data: {
        user: {
          id: user._id,
          name: user.name,
          phone: user.phone,
          email: user.email,
          role: user.role,
          loyaltyPoints: user.loyaltyPoints,
          referralCode: user.referralCode,
          addresses: user.addresses,
          isNewUser
        },
        token
      }
    });

  } catch (error) {
    next(error);
  }
};

// Resend OTP
const resendOTP = async (req, res, next) => {
  try {
    const { phone } = req.body;

    const user = await User.findOne({ phone });
    
    if (!user) {
      return res.status(400).json({
        success: false,
        message: 'User not found'
      });
    }

    // Check if enough time has passed (30 seconds cooldown)
    if (user.otpExpiry && Date.now() < user.otpExpiry - 4.5 * 60 * 1000) {
      return res.status(429).json({
        success: false,
        message: 'Please wait before requesting another OTP'
      });
    }

    // Generate and save new OTP
    const otp = user.generateOTP();
    await user.save({ validateBeforeSave: false });

    // Send OTP via SMS
    const smsResult = await smsService.sendOTP(phone, otp);
    
    if (!smsResult.success) {
      return res.status(500).json({
        success: false,
        message: 'Failed to send OTP. Please try again.'
      });
    }

    res.status(200).json({
      success: true,
      message: 'OTP resent successfully',
      data: {
        otpSent: true,
        ...(process.env.NODE_ENV === 'development' && { otp })
      }
    });

  } catch (error) {
    next(error);
  }
};

// Get current user profile
const getProfile = async (req, res, next) => {
  try {
    const user = req.user;

    res.status(200).json({
      success: true,
      data: {
        user: {
          id: user._id,
          name: user.name,
          phone: user.phone,
          email: user.email,
          role: user.role,
          loyaltyPoints: user.loyaltyPoints,
          referralCode: user.referralCode,
          addresses: user.addresses,
          defaultAddress: user.defaultAddress,
          preferences: user.preferences,
          createdAt: user.createdAt
        }
      }
    });

  } catch (error) {
    next(error);
  }
};

// Update user profile
const updateProfile = async (req, res, next) => {
  try {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({
        success: false,
        message: 'Validation error',
        errors: errors.array()
      });
    }

    const { name, email } = req.body;
    const user = req.user;

    if (name) user.name = name;
    if (email) user.email = email;

    await user.save();

    res.status(200).json({
      success: true,
      message: 'Profile updated successfully',
      data: {
        user: {
          id: user._id,
          name: user.name,
          phone: user.phone,
          email: user.email,
          role: user.role,
          loyaltyPoints: user.loyaltyPoints
        }
      }
    });

  } catch (error) {
    next(error);
  }
};

// Logout user
const logout = async (req, res, next) => {
  try {
    res.cookie('token', '', {
      expires: new Date(0),
      httpOnly: true
    });

    res.status(200).json({
      success: true,
      message: 'Logged out successfully'
    });

  } catch (error) {
    next(error);
  }
};

// Validation rules
const sendOTPValidation = [
  body('phone')
    .matches(/^[6-9]\d{9}$/)
    .withMessage('Please provide a valid Indian mobile number')
];

const verifyOTPValidation = [
  body('phone')
    .matches(/^[6-9]\d{9}$/)
    .withMessage('Please provide a valid Indian mobile number'),
  body('otp')
    .isLength({ min: 6, max: 6 })
    .isNumeric()
    .withMessage('OTP must be 6 digits'),
  body('name')
    .optional()
    .trim()
    .isLength({ min: 2, max: 50 })
    .withMessage('Name must be between 2-50 characters'),
  body('referredBy')
    .optional()
    .trim()
    .isLength({ min: 6, max: 8 })
    .withMessage('Invalid referral code')
];

const updateProfileValidation = [
  body('name')
    .optional()
    .trim()
    .isLength({ min: 2, max: 50 })
    .withMessage('Name must be between 2-50 characters'),
  body('email')
    .optional()
    .isEmail()
    .withMessage('Please provide a valid email')
];

module.exports = {
  sendOTP,
  verifyOTP,
  resendOTP,
  getProfile,
  updateProfile,
  logout,
  sendOTPValidation,
  verifyOTPValidation,
  updateProfileValidation
};
