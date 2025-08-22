const mongoose = require('mongoose');

const variantSchema = new mongoose.Schema({
  size: String, // e.g., "500g", "1kg", "500ml"
  unit: {
    type: String,
    enum: ['kg', 'g', 'l', 'ml', 'piece', 'packet', 'dozen'],
    required: true
  },
  quantity: {
    type: Number,
    required: true
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
    discount: {
      type: Number,
      default: 0
    }
  },
  stock: {
    type: Number,
    required: true,
    min: 0
  },
  sku: {
    type: String,
    unique: true,
    required: true
  },
  isDefault: {
    type: Boolean,
    default: false
  }
});

const nutritionSchema = new mongoose.Schema({
  energy: Number, // kcal per 100g/100ml
  protein: Number, // g per 100g/100ml
  carbs: Number,
  fat: Number,
  fiber: Number,
  sugar: Number,
  sodium: Number
});

const productSchema = new mongoose.Schema({
  name: {
    type: String,
    required: [true, 'Product name is required'],
    maxlength: [100, 'Product name cannot exceed 100 characters'],
    text: true // Enable text index for search
  },
  slug: {
    type: String,
    required: true,
    unique: true
  },
  description: {
    type: String,
    maxlength: [2000, 'Description cannot exceed 2000 characters']
  },
  shortDescription: {
    type: String,
    maxlength: [200, 'Short description cannot exceed 200 characters']
  },
  category: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'Category',
    required: [true, 'Product category is required']
  },
  brand: String,
  images: [{
    public_id: String,
    url: {
      type: String,
      required: true
    }
  }],
  variants: {
    type: [variantSchema],
    validate: {
      validator: function(variants) {
        return variants.length > 0;
      },
      message: 'Product must have at least one variant'
    }
  },
  tags: [String], // For better search and filtering
  ingredients: [String],
  nutrition: nutritionSchema,
  
  // SEO
  metaTitle: String,
  metaDescription: String,
  
  // Product flags
  isOrganic: { type: Boolean, default: false },
  isFeatured: { type: Boolean, default: false },
  isActive: { type: Boolean, default: true },
  isVegetarian: { type: Boolean, default: true },
  
  // Inventory alerts
  lowStockThreshold: { type: Number, default: 10 },
  
  // Ratings and reviews
  averageRating: { type: Number, default: 0, min: 0, max: 5 },
  numReviews: { type: Number, default: 0 },
  
  // Sales data
  totalSold: { type: Number, default: 0 },
  
  // Delivery info
  maxDeliveryTime: { type: Number, default: 30 }, // in minutes
  
  // Expiry and handling
  shelfLife: String, // e.g., "6 months", "1 year"
  storageInstructions: String,
  
  // Admin fields
  addedBy: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User',
    required: true
  },
  
  // Timestamps for offers/deals
  dealStartDate: Date,
  dealEndDate: Date,
  
  // Search optimization
  searchKeywords: [String]
}, {
  timestamps: true,
  toJSON: { virtuals: true },
  toObject: { virtuals: true }
});

// Indexes for better performance
productSchema.index({ name: 'text', description: 'text', tags: 'text' });
productSchema.index({ category: 1, isActive: 1 });
productSchema.index({ isFeatured: 1, isActive: 1 });
productSchema.index({ 'variants.price.sellingPrice': 1 });
productSchema.index({ averageRating: -1 });
productSchema.index({ totalSold: -1 });
productSchema.index({ createdAt: -1 });

// Virtual for discount percentage (using default variant)
productSchema.virtual('discountPercentage').get(function() {
  const defaultVariant = this.variants.find(v => v.isDefault) || this.variants[0];
  if (defaultVariant) {
    const { mrp, sellingPrice } = defaultVariant.price;
    return Math.round(((mrp - sellingPrice) / mrp) * 100);
  }
  return 0;
});

// Virtual for stock status
productSchema.virtual('stockStatus').get(function() {
  const totalStock = this.variants.reduce((total, variant) => total + variant.stock, 0);
  if (totalStock === 0) return 'out_of_stock';
  if (totalStock <= this.lowStockThreshold) return 'low_stock';
  return 'in_stock';
});

// Virtual for price range
productSchema.virtual('priceRange').get(function() {
  if (this.variants.length === 0) return null;
  
  const prices = this.variants.map(v => v.price.sellingPrice);
  const min = Math.min(...prices);
  const max = Math.max(...prices);
  
  return { min, max };
});

// Pre-save middleware to generate slug and set default variant
productSchema.pre('save', function(next) {
  // Generate slug from name
  if (this.isModified('name')) {
    this.slug = this.name
      .toLowerCase()
      .replace(/[^a-zA-Z0-9]/g, '-')
      .replace(/-+/g, '-')
      .replace(/^-|-$/g, '');
  }
  
  // Ensure at least one variant is default
  if (this.variants.length > 0) {
    const hasDefault = this.variants.some(v => v.isDefault);
    if (!hasDefault) {
      this.variants[0].isDefault = true;
    }
  }
  
  // Generate search keywords
  this.searchKeywords = [
    ...this.name.toLowerCase().split(' '),
    ...this.tags.map(tag => tag.toLowerCase()),
    this.brand?.toLowerCase(),
    this.category?.toString()
  ].filter(Boolean);
  
  next();
});

// Static method for advanced search
productSchema.statics.searchProducts = async function(searchTerm, filters = {}) {
  const query = { isActive: true };
  
  // Text search
  if (searchTerm) {
    query.$text = { $search: searchTerm };
  }
  
  // Category filter
  if (filters.category) {
    query.category = filters.category;
  }
  
  // Price range filter
  if (filters.minPrice || filters.maxPrice) {
    query['variants.price.sellingPrice'] = {};
    if (filters.minPrice) query['variants.price.sellingPrice'].$gte = filters.minPrice;
    if (filters.maxPrice) query['variants.price.sellingPrice'].$lte = filters.maxPrice;
  }
  
  // Brand filter
  if (filters.brand) {
    query.brand = new RegExp(filters.brand, 'i');
  }
  
  // Organic filter
  if (filters.isOrganic) {
    query.isOrganic = true;
  }
  
  // In stock filter
  if (filters.inStock) {
    query['variants.stock'] = { $gt: 0 };
  }
  
  let sortOption = {};
  
  // Sort options
  switch (filters.sortBy) {
    case 'price_low_high':
      sortOption = { 'variants.price.sellingPrice': 1 };
      break;
    case 'price_high_low':
      sortOption = { 'variants.price.sellingPrice': -1 };
      break;
    case 'rating':
      sortOption = { averageRating: -1 };
      break;
    case 'popularity':
      sortOption = { totalSold: -1 };
      break;
    case 'newest':
      sortOption = { createdAt: -1 };
      break;
    default:
      if (searchTerm) {
        sortOption = { score: { $meta: 'textScore' } };
      } else {
        sortOption = { isFeatured: -1, createdAt: -1 };
      }
  }
  
  return this.find(query)
    .populate('category')
    .sort(sortOption)
    .limit(filters.limit || 50);
};

// Method to update stock
productSchema.methods.updateStock = function(variantId, quantity) {
  const variant = this.variants.id(variantId);
  if (variant) {
    variant.stock += quantity;
    return this.save();
  }
  throw new Error('Variant not found');
};

// Method to check availability
productSchema.methods.isAvailable = function(variantId, quantity = 1) {
  const variant = this.variants.id(variantId);
  return variant && variant.stock >= quantity;
};

module.exports = mongoose.model('Product', productSchema);
