const notFound = (req, res, next) => {
  res.status(404).json({
    success: false,
    message: `Route ${req.originalUrl} not found`,
    availableRoutes: {
      auth: '/api/auth',
      users: '/api/users',
      products: '/api/products',
      categories: '/api/categories',
      cart: '/api/cart',
      orders: '/api/orders',
      delivery: '/api/delivery',
      admin: '/api/admin',
      payment: '/api/payment',
      health: '/api/health'
    }
  });
};

module.exports = notFound;
