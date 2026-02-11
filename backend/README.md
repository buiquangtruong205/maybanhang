# Vending Machine API & Simulator

API backend cho máy bán hàng tự động với tích hợp PayOS và simulator ESP32.

## 🚀 Cài đặt và chạy

### 1. Cài đặt dependencies
```bash
cd payment_service
pip install -r requirements.txt
```

### 2. Cấu hình environment
Tạo file `.env` trong thư mục `payment_service`:
```env
PAYOS_CLIENT_ID=your_client_id
PAYOS_API_KEY=your_api_key
PAYOS_CHECKSUM_KEY=your_checksum_key
DOMAIN=http://172.16.1.217:5000
PORT=5000
```

### 3. Chạy server
```bash
python run_server.py
```

Server sẽ chạy tại: http://172.16.1.217:5000

## 📋 API Endpoints

### Products API
- `GET /api/products` - Lấy danh sách tất cả sản phẩm
- `GET /api/products/{id}` - Lấy thông tin sản phẩm theo ID
- `PUT /api/products/{id}/stock?new_stock=10` - Cập nhật stock sản phẩm
- `POST /api/products/{id}/purchase` - Mua sản phẩm (giảm stock)

### Payment API
- `POST /api/create-payment` - Tạo thanh toán mới
- `GET /api/order-status/{order_code}` - Kiểm tra trạng thái đơn hàng
- `POST /api/dispense-complete` - Xác nhận xuất hàng thành công
- `POST /api/heartbeat` - Nhận heartbeat từ máy

### Web Interface
- `GET /` - Trang chủ demo thanh toán
- `GET /success` - Trang thành công
- `GET /cancel` - Trang hủy thanh toán

## 🤖 ESP32 Simulator

### Chạy simulator
```bash
python simulator.py
```

### Chức năng simulator:
1. **Hiển thị sản phẩm** - Load từ API thật
2. **Reload sản phẩm** - Tải lại từ API
3. **Tạo thanh toán** - Tạo QR code PayOS
4. **Kiểm tra thanh toán** - Check trạng thái real-time
5. **Giả lập xuất hàng** - Simulate dispensing
6. **Cập nhật stock** - Sync với API
7. **Test API** - Kiểm tra tất cả endpoints

## 🧪 Testing

### Test API nhanh
```bash
python test_api.py
```

### Test manual
1. Chạy server: `python run_server.py`
2. Mở browser: http://172.16.1.217:5000/docs (Swagger UI)
3. Test API: http://172.16.1.217:5000/api/products

## 📦 Dữ liệu sản phẩm mẫu

API cung cấp 8 sản phẩm mẫu:
- Coca Cola, Pepsi, Sprite, Fanta (15k-12k VND)
- Aquafina, Lavie (8k VND)
- Snack Oishi (10k VND)
- Bánh Oreo (18k VND)

## 🔄 Workflow hoàn chỉnh

1. **ESP32** gửi heartbeat định kỳ
2. **User** chọn sản phẩm trên màn hình
3. **ESP32** gọi API tạo thanh toán
4. **API** tạo QR PayOS và trả về
5. **User** scan QR và thanh toán
6. **ESP32** polling check trạng thái
7. **Khi PAID** → ESP32 xuất hàng
8. **ESP32** gửi xác nhận xuất hàng thành công

## 🛠️ Development

### Cấu trúc thư mục
```
payment_service/
├── app/
│   ├── models/          # Data models
│   ├── routers/         # API routes
│   ├── services/        # Business logic
│   └── config.py        # Configuration
├── main.py              # FastAPI app
├── run_server.py        # Development server
├── simulator.py         # ESP32 simulator
├── test_api.py          # API testing
└── requirements.txt     # Dependencies
```

### Thêm sản phẩm mới
Chỉnh sửa `app/models/product.py` → `SAMPLE_PRODUCTS`

### Thêm API mới
1. Tạo router trong `app/routers/`
2. Import và include trong `main.py`

## 🔧 Troubleshooting

### Lỗi kết nối API
- Kiểm tra server đang chạy: http://172.16.1.217:5000
- Kiểm tra firewall/network
- Thử IP khác nếu cần

### Lỗi PayOS
- Kiểm tra credentials trong `.env`
- Xem log server để debug
- Test với Postman/curl

### Simulator không hoạt động
- Kiểm tra backend URL trong simulator
- Chạy `test_api.py` để verify endpoints
- Kiểm tra network connectivity