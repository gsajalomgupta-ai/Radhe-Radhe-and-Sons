const twilio = require('twilio');

class SMSService {
  constructor() {
    this.client = twilio(
      process.env.TWILIO_ACCOUNT_SID,
      process.env.TWILIO_AUTH_TOKEN
    );
    this.fromNumber = process.env.TWILIO_PHONE_NUMBER;
  }

  async sendOTP(phone, otp) {
    try {
      const message = `Your Radhe Radhe & Sons verification code is: ${otp}. Valid for 5 minutes. Do not share with anyone.`;
      
      const result = await this.client.messages.create({
        body: message,
        from: this.fromNumber,
        to: `+91${phone}`
      });

      console.log(`OTP sent to ${phone}: ${result.sid}`);
      return { success: true, messageId: result.sid };
    } catch (error) {
      console.error('SMS Error:', error);
      return { success: false, error: error.message };
    }
  }

  async sendOrderConfirmation(phone, orderNumber, estimatedTime) {
    try {
      const message = `Order ${orderNumber} confirmed! Your groceries will be delivered in approximately ${estimatedTime} minutes. Track your order in the app. - Radhe Radhe & Sons`;
      
      const result = await this.client.messages.create({
        body: message,
        from: this.fromNumber,
        to: `+91${phone}`
      });

      return { success: true, messageId: result.sid };
    } catch (error) {
      console.error('SMS Error:', error);
      return { success: false, error: error.message };
    }
  }

  async sendOrderUpdate(phone, orderNumber, status, message = '') {
    try {
      const statusMessages = {
        'packed': `Order ${orderNumber} is packed and ready for delivery!`,
        'out_for_delivery': `Order ${orderNumber} is out for delivery. Our delivery partner will reach you soon.`,
        'delivered': `Order ${orderNumber} has been delivered successfully. Thank you for choosing Radhe Radhe & Sons!`,
        'cancelled': `Order ${orderNumber} has been cancelled. ${message}`,
      };

      const smsText = statusMessages[status] || `Order ${orderNumber} status: ${status}. ${message}`;
      
      const result = await this.client.messages.create({
        body: smsText,
        from: this.fromNumber,
        to: `+91${phone}`
      });

      return { success: true, messageId: result.sid };
    } catch (error) {
      console.error('SMS Error:', error);
      return { success: false, error: error.message };
    }
  }

  async sendDeliveryOTP(phone, otp, orderNumber) {
    try {
      const message = `Delivery OTP for order ${orderNumber}: ${otp}. Share this with the delivery partner for order completion. - Radhe Radhe & Sons`;
      
      const result = await this.client.messages.create({
        body: message,
        from: this.fromNumber,
        to: `+91${phone}`
      });

      return { success: true, messageId: result.sid };
    } catch (error) {
      console.error('SMS Error:', error);
      return { success: false, error: error.message };
    }
  }

  async sendWelcomeMessage(phone, name, referralCode) {
    try {
      const message = `Welcome to Radhe Radhe & Sons, ${name}! 🛒 Your referral code: ${referralCode}. Share with friends to earn rewards. Start shopping fresh groceries now!`;
      
      const result = await this.client.messages.create({
        body: message,
        from: this.fromNumber,
        to: `+91${phone}`
      });

      return { success: true, messageId: result.sid };
    } catch (error) {
      console.error('SMS Error:', error);
      return { success: false, error: error.message };
    }
  }

  async sendPromoMessage(phone, promoCode, discount, validUntil) {
    try {
      const message = `🎉 Special offer! Use code ${promoCode} and get ${discount}% off. Valid until ${validUntil}. Order now on Radhe Radhe & Sons app!`;
      
      const result = await this.client.messages.create({
        body: message,
        from: this.fromNumber,
        to: `+91${phone}`
      });

      return { success: true, messageId: result.sid };
    } catch (error) {
      console.error('SMS Error:', error);
      return { success: false, error: error.message };
    }
  }
}

module.exports = new SMSService();
