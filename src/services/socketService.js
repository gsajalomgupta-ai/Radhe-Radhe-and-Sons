class SocketService {
  constructor() {
    this.io = null;
    this.connectedUsers = new Map(); // userId -> socketId
    this.connectedDeliveryPartners = new Map(); // partnerId -> socketId
  }

  initializeSocket(io) {
    this.io = io;
    
    io.on('connection', (socket) => {
      console.log(`Socket connected: ${socket.id}`);
      
      // User authentication
      socket.on('authenticate', (data) => {
        const { userId, role } = data;
        
        if (role === 'delivery_partner') {
          this.connectedDeliveryPartners.set(userId, socket.id);
          socket.join(`delivery_${userId}`);
          console.log(`Delivery partner ${userId} connected`);
        } else {
          this.connectedUsers.set(userId, socket.id);
          socket.join(`user_${userId}`);
          console.log(`User ${userId} connected`);
        }
        
        socket.userId = userId;
        socket.userRole = role;
      });
      
      // Handle delivery partner location updates
      socket.on('update_location', (data) => {
        const { latitude, longitude, orderId } = data;
        
        if (socket.userRole === 'delivery_partner') {
          // Broadcast location to the customer
          socket.broadcast.to(`order_${orderId}`).emit('delivery_location_update', {
            latitude,
            longitude,
            timestamp: new Date()
          });
        }
      });
      
      // Handle order tracking subscription
      socket.on('track_order', (orderId) => {
        socket.join(`order_${orderId}`);
        console.log(`Socket ${socket.id} tracking order ${orderId}`);
      });
      
      // Handle disconnection
      socket.on('disconnect', () => {
        console.log(`Socket disconnected: ${socket.id}`);
        
        if (socket.userId) {
          if (socket.userRole === 'delivery_partner') {
            this.connectedDeliveryPartners.delete(socket.userId);
          } else {
            this.connectedUsers.delete(socket.userId);
          }
        }
      });
    });
  }

  // Send order status update to customer
  sendOrderUpdate(userId, orderData) {
    if (this.io) {
      this.io.to(`user_${userId}`).emit('order_status_update', {
        orderId: orderData._id,
        orderNumber: orderData.orderNumber,
        status: orderData.status,
        message: orderData.tracking[orderData.tracking.length - 1]?.note,
        timestamp: new Date(),
        estimatedDeliveryTime: orderData.estimatedDeliveryTime
      });
    }
  }

  // Send new order notification to admin/delivery partners
  sendNewOrderNotification(orderData) {
    if (this.io) {
      // Notify all admins
      this.io.emit('new_order', {
        orderId: orderData._id,
        orderNumber: orderData.orderNumber,
        customerName: orderData.user?.name,
        totalAmount: orderData.orderSummary.totalAmount,
        itemsCount: orderData.orderSummary.itemsCount,
        deliveryAddress: orderData.deliveryAddress.fullAddress,
        timestamp: orderData.createdAt
      });
    }
  }

  // Send delivery assignment notification
  sendDeliveryAssignment(partnerId, orderData) {
    if (this.io) {
      this.io.to(`delivery_${partnerId}`).emit('delivery_assigned', {
        orderId: orderData._id,
        orderNumber: orderData.orderNumber,
        customerName: orderData.user?.name,
        customerPhone: orderData.contactNumber,
        deliveryAddress: orderData.deliveryAddress,
        totalAmount: orderData.orderSummary.totalAmount,
        estimatedDeliveryTime: orderData.estimatedDeliveryTime,
        deliveryOTP: orderData.deliveryOTP
      });
    }
  }

  // Send real-time inventory update
  sendInventoryUpdate(productId, stock) {
    if (this.io) {
      this.io.emit('inventory_update', {
        productId,
        stock,
        timestamp: new Date()
      });
    }
  }

  // Send promotional notifications
  sendPromoNotification(userId, promoData) {
    if (this.io && userId) {
      this.io.to(`user_${userId}`).emit('promotion', {
        title: promoData.title,
        message: promoData.message,
        couponCode: promoData.couponCode,
        discount: promoData.discount,
        validUntil: promoData.validUntil,
        timestamp: new Date()
      });
    } else if (this.io) {
      // Broadcast to all users
      this.io.emit('promotion', promoData);
    }
  }

  // Send delivery partner location update to customer
  sendLocationUpdate(orderId, locationData) {
    if (this.io) {
      this.io.to(`order_${orderId}`).emit('delivery_location_update', {
        latitude: locationData.latitude,
        longitude: locationData.longitude,
        timestamp: new Date(),
        estimatedArrival: locationData.estimatedArrival
      });
    }
  }

  // Send low stock alert to admins
  sendLowStockAlert(productData) {
    if (this.io) {
      this.io.emit('low_stock_alert', {
        productId: productData._id,
        productName: productData.name,
        currentStock: productData.variants.reduce((total, v) => total + v.stock, 0),
        threshold: productData.lowStockThreshold,
        timestamp: new Date()
      });
    }
  }

  // Send chat message
  sendChatMessage(recipientId, messageData) {
    if (this.io) {
      this.io.to(`user_${recipientId}`).emit('chat_message', {
        senderId: messageData.senderId,
        message: messageData.message,
        timestamp: new Date(),
        orderId: messageData.orderId
      });
    }
  }

  // Get connected users count
  getConnectedUsersCount() {
    return this.connectedUsers.size;
  }

  // Get connected delivery partners count
  getConnectedDeliveryPartnersCount() {
    return this.connectedDeliveryPartners.size;
  }

  // Check if user is online
  isUserOnline(userId) {
    return this.connectedUsers.has(userId);
  }

  // Check if delivery partner is online
  isDeliveryPartnerOnline(partnerId) {
    return this.connectedDeliveryPartners.has(partnerId);
  }
}

module.exports = new SocketService();
