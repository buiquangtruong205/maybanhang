# Công Việc Cần Làm

## Ưu tiên rất cao

1. Khóa các endpoint thay đổi trạng thái đơn hàng
- File: `backend/app/routes/order.py`
- Vấn đề: `/orders/<id>/complete` và `/orders/<id>/cancel` đang public.
- Cần làm: thêm auth phù hợp hoặc chỉ cho phép internal flow/payment service gọi.

2. Sửa luồng thanh toán để server làm nguồn dữ liệu duy nhất
- File: `backend/app/routes/payment.py`
- Vấn đề: client đang gửi `amount`, `items`, `description`, `order_code`; backend tin dữ liệu này.
- Cần làm: frontend chỉ gửi `order_id`, backend tự truy DB để tạo request PayOS và đối chiếu số tiền khi webhook/poll về.

3. Ràng buộc đơn hàng với đúng máy IoT
- File: `backend/app/routes/iot.py`
- Vấn đề: một máy có thể đọc/cập nhật đơn của máy khác nếu biết `order_id`.
- Cần làm: kiểm tra `order -> slot -> machine_id` trước khi cho phép `dispense_complete`, `check_order_payment`, và các route liên quan.

4. Khóa endpoint tạo transaction public
- File: `backend/app/routes/transaction.py`
- Vấn đề: `POST /transactions` không cần auth.
- Cần làm: bỏ endpoint này hoặc chỉ cho internal service/webhook được ghi transaction.

5. Siết auth cho thiết bị IoT
- File: `backend/app/config.py`, `backend/app/utils/machine_auth.py`
- Vấn đề: key tĩnh `may1`, `may2` quá yếu và còn nhận qua query/body.
- Cần làm: chuyển secret vào DB/env, chỉ nhận qua header, tốt hơn là HMAC hoặc session token cho thiết bị.

## Ưu tiên cao

6. Ẩn hoặc bảo vệ route admin
- File: `backend/app/__init__.py`
- Vấn đề: `/admin` đang public.
- Cần làm: thêm lớp bảo vệ cho admin UI hoặc đưa sau reverse proxy có auth.

7. Bỏ fallback secret và siết CORS
- File: `backend/app/config.py`, `backend/app/__init__.py`
- Vấn đề: `SECRET_KEY` có fallback mặc định, `CORS_ORIGINS` mặc định là `*`.
- Cần làm: fail-fast khi thiếu env quan trọng, chỉ cho phép origin cụ thể.

8. Rotate toàn bộ secret đã lộ
- File: `.env`
- Vấn đề: `.env` đang chứa khóa thật.
- Cần làm: đổi `SECRET_KEY`, PayOS keys và mọi credential đã từng lộ hoặc commit.

## Ưu tiên trung bình

9. Xử lý race condition tồn kho/pending order
- File: `backend/app/routes/order.py`, `backend/app/routes/payment.py`, `backend/app/routes/iot.py`
- Vấn đề: tính `pending_qty` và trừ stock chưa có row lock thật.
- Cần làm: dùng transaction + row locking hoặc cơ chế reserved stock riêng.

10. Sửa comment sai về `with_for_update`
- File: `backend/app/routes/payment.py`
- Vấn đề: comment nói đã dùng lock nhưng thực tế chưa dùng.
- Cần làm: hoặc thêm lock thật, hoặc sửa comment để không gây hiểu nhầm.

11. Sửa thống kê dashboard
- File: `backend/app/routes/stats.py`
- Vấn đề:
  - `start_of_month` được tạo nhưng không dùng.
  - `Transaction.status == 'completed'` không khớp với dữ liệu đang ghi là `success`.
- Cần làm: thống nhất trạng thái transaction và filter đúng theo tháng.

12. Kiểm tra lại Docker backend startup
- File: `backend/Dockerfile`, `requirements.txt`
- Vấn đề: Dockerfile dùng `eventlet`; cần chắc dependency tương ứng có thật và startup ổn định.
- Cần làm: đồng bộ `Dockerfile` với dependencies thực tế.

## Ghi chú hiện tại

- Passkey đã được khôi phục trong code nhưng đang ẩn khỏi UI đăng nhập.
- Hiện tại hệ thống dùng đăng nhập bình thường bằng `username/password`.
- Khi cần bật lại Passkey, chỉ cần mở lại phần UI mà không phải viết lại backend.
