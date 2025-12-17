# 📧 Thông tin liên hệ PayOS Support

## 🔥 VẤN ĐỀ HIỆN TẠI:
- **Lỗi:** PayOS API trả về "code 20 - Thông tin truyền lên không đúng"
- **Endpoint:** https://api-merchant.payos.vn/v2/payment-requests
- **Method:** POST
- **Status:** 200 OK nhưng code=20

## 📋 THÔNG TIN GỬI CHO SUPPORT:

**Subject:** [URGENT] PayOS API Error Code 20 - Thông tin truyền lên không đúng

**Nội dung:**
```
Chào team PayOS,

Tôi đang gặp vấn đề với PayOS API khi tạo payment request:

1. CLIENT_ID: f63d926b-644a-4bcb-93e0-b13efa63a982
2. API_KEY: 4723b251-ffe5-4476-96d5-0c4c5e9896e8
3. CHECKSUM_KEY: 1008ed05145eac506739b65893eb99000379f58862054641a6de585201be690a

PAYLOAD GỬI:
{
  "orderCode": 1765900495,
  "amount": 50000,
  "description": "Thanh toán đơn #1765900495",
  "items": [
    {
      "name": "Đơn hàng #1765900495",
      "quantity": 1,
      "price": 50000
    }
  ],
  "returnUrl": "http://localhost:5000/success",
  "cancelUrl": "http://localhost:5000/cancel"
}

RESPONSE NHẬN ĐƯỢC:
{
  "code": "20",
  "desc": "Thông tin truyền lên không đúng.",
  "data": null
}

Tôi đã thử:
- Nhiều endpoint khác nhau
- Với và không có signature
- Format payload khác nhau
- Tài khoản đã được kích hoạt trên web dashboard

Xin hỗ trợ kiểm tra tài khoản và API credentials.

Cảm ơn!
```

## 📞 KÊNH LIÊN HỆ:

1. **Email:** support@payos.vn
2. **Hotline:** 1900 6173
3. **Website:** https://payos.vn/support
4. **Facebook:** https://facebook.com/payosvn

## ⏰ THỜI GIAN HỖ TRỢ:
- Thứ 2 - Thứ 6: 8:00 - 17:30
- Thứ 7: 8:00 - 12:00

## 🔧 TRONG KHI CHỜ SUPPORT:

Bạn có thể sử dụng hệ thống hiện tại với mã QR chuyển khoản ngân hàng để nhận thanh toán thực tế.