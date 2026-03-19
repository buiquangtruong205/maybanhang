# Giao Diện Máy Bán Hàng

Đây là frontend tĩnh cho giao diện máy bán hàng.

Ứng dụng chạy bằng HTML, CSS và JavaScript thuần, không dùng bundler. Client đọc cấu hình từ `js/env.js`, gọi backend API và theo dõi trạng thái thanh toán theo thời gian thực.

## Cấu trúc

```text
CLIENT_machine/
  index.html
  style.css
  js/
    app.js
    api.js
    cart.js
    config.js
    env.example.js
    env.js
    payment.js
    ui.js
    websocket.js
  README.md
```

## Vai trò các file

- `index.html`
  Khung giao diện chính.
- `style.css`
  Toàn bộ style của giao diện máy bán hàng.
- `js/config.js`
  Cấu hình runtime phía client.
- `js/env.example.js`
  File mẫu cho cấu hình cục bộ.
- `js/env.js`
  File cấu hình thực tế trên máy.
- `js/api.js`
  Hàm gọi backend.
- `js/cart.js`
  Quản lý giỏ hàng.
- `js/payment.js`
  Luồng tạo payment và theo dõi thanh toán.
- `js/ui.js`
  Render UI và cập nhật DOM.
- `js/websocket.js`
  Kết nối WebSocket/Socket.IO.
- `js/app.js`
  Entry point khởi tạo ứng dụng.

## Cấu hình

Tạo hoặc chỉnh [js/env.js](E:\IoT\Du_An\Vending_Machine\Vesion_3\CLIENT_machine\js\env.js) từ file mẫu [js/env.example.js](E:\IoT\Du_An\Vending_Machine\Vesion_3\CLIENT_machine\js\env.example.js).

Các giá trị cần kiểm tra:

- API base URL
- machine key
- machine id
- endpoint WebSocket nếu khác mặc định

## Chạy

Cách đơn giản nhất:

- mở [index.html](E:\IoT\Du_An\Vending_Machine\Vesion_3\CLIENT_machine\index.html) trong trình duyệt

Nếu gặp lỗi CORS hoặc policy của trình duyệt, phục vụ thư mục này bằng web server tĩnh local.

## Phụ thuộc phía hệ thống

Frontend này cần backend hoạt động đúng ở các luồng:

- lấy danh sách sản phẩm hoặc slot
- tạo order
- tạo payment
- polling hoặc websocket cho trạng thái thanh toán
- heartbeat hoặc session của frontend machine

## Ghi chú

- Đây là giao diện cho máy bán hàng, không phải dashboard admin.
- Dashboard admin nằm trong [backend/app/static](E:\IoT\Du_An\Vending_Machine\Vesion_3\backend\app\static).
