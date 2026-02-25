# 🖼️ Đặc Tả Luồng Giao Diện Frontend — Mô Hình Hybrid

> Tài liệu này mô tả vai trò của Trang Web (Frontend) trong mô hình Hybrid:  
> **Kênh 1** — Mua tại máy (nút bấm + OLED trên ESP32)  
> **Kênh 2** — Mua online qua web, nhận hàng tại máy

---

## 📝 Quy Tắc Chung
- **Ngôn ngữ:** Tiếng Việt 100%.
- **Vai trò Frontend:** Là **Kênh 2** — giao diện mua hàng online (điện thoại/máy tính).
- **Mục đích:** Cho phép khách hàng xem sản phẩm, thanh toán từ xa và kích hoạt nhả hàng.

---

## 🔄 1. Luồng Mua Hàng Online (Kênh 2)

### Bước 1: Chọn sản phẩm (`HomeView.vue`)
- Khách hàng truy cập URL của máy bán hàng (có thể quét QR code trên thân máy).
- **Kiểm tra trạng thái máy:** Nếu máy `offline` → hiển thị banner "Máy tạm ngừng phục vụ" và khóa nút mua.
- Khách chọn sản phẩm và nhấn "Mua hàng".

### Bước 2: Thanh toán (`PaymentView.vue`)
- Frontend hiển thị QR Code PayOS.
- Khách thanh toán trên app ngân hàng.
- Frontend polling hoặc lắng nghe Socket.IO để kiểm tra trạng thái.

### Bước 3: Nhả hàng (Backend → ESP32)
- Backend nhận thanh toán → Gửi lệnh MQTT tới ESP32 → Máy nhả hàng.
- Frontend hiển thị: **"Đã nhận thanh toán! Máy đang nhả hàng..."**

### Bước 4: Hoàn tất
- ESP32 báo cáo kết quả → Backend → Socket.IO → Frontend.
- Hiển thị: **"Thành công! Vui lòng nhận sản phẩm tại máy."**

---

## 🟢 2. Hiển Thị Trạng Thái Máy

| Trạng thái | Hiển thị trên Web | Cho phép mua? |
| :--- | :--- | :--- |
| `online` | Chấm xanh 🟢 "Máy đang hoạt động" | ✅ Có |
| `offline` | Banner đỏ 🔴 "Máy tạm ngừng, vui lòng quay lại sau" | ❌ Không |
| `dispensing` | Chữ vàng 🟡 "Máy đang xử lý đơn hàng khác..." | ⏳ Chờ |

---

## 📡 3. Sự Kiện Socket.IO

| Sự kiện | Hướng | Hành động của Frontend |
| :--- | :--- | :--- |
| `machine_status` | Backend → Web | Cập nhật nhãn Online/Offline trên trang chủ |
| `order_update` | Backend → Web | Chuyển sang màn hình "Đang nhả hàng" |
| `dispense_result` | Backend → Web | Thông báo thành công hoặc lỗi kẹt hàng |

---

## 💡 4. Khuyến Nghị UX

1. **Vị trí máy:** Hiển thị rõ địa chỉ máy (vd: "Tầng 1, Tòa nhà A") để khách biết nhận hàng ở đâu.
2. **Hướng dẫn:** Sau khi thanh toán: "Vui lòng đợi 5-10 giây để máy nhả hàng."
3. **Hotline:** Hiển thị số điện thoại hỗ trợ ở trang kết quả để xử lý sự cố.
4. **QR trên thân máy:** In QR code dẫn tới URL trang web, dán trên mặt trước máy để khách quét khi đứng trước máy.

---
*Tài liệu này mô tả Kênh 2 (Web) trong mô hình Hybrid. Kênh 1 (Tại máy) được mô tả trong `FIRMWARE_ROADMAP.md`.*
