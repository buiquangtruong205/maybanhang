# Payment Test Scripts

Các script trong thư mục này dùng để kiểm tra thủ công luồng thanh toán online của backend.

## Các file

- `manual_payment_test_suite.py`
  Script chạy chung. Hỗ trợ:
  - `--mode success`: chạy luồng thành công
  - `--mode negative`: chạy luồng lỗi/regression
  - `--mode all`: chạy cả hai

- `manual_payment_flow_test.py`
  Script test riêng luồng thành công:
  - tạo pending order
  - tạo payment link
  - giả lập webhook thành công
  - kiểm tra duplicate webhook
  - kiểm tra trạng thái order/payment
  - kiểm tra `iot/pending-orders`
  - tùy chọn gọi `dispense-complete`

- `manual_payment_negative_test.py`
  Script test riêng các case lỗi:
  - amount sai
  - cancel xong thì order phải `cancelled`
  - webhook đến sau khi cancel phải bị chặn
  - order `completed` không được tạo payment lại
  - duplicate webhook phải được bỏ qua

## Yêu cầu

- Backend đang chạy, ví dụ tại `http://localhost:5000`
- Dữ liệu `product_id`, `slot_id`, `machine_key`, `slot_code` phải tồn tại đúng trong hệ thống
- Nếu test có phần IoT thì máy/slot phải map đúng với order

## Cách chạy nhanh

### 1. Chạy toàn bộ suite

```bash
python3 backend/scripts/manual_payment_test_suite.py \
  --mode all \
  --base-url http://localhost:5000 \
  --product-id 1 \
  --price 10000 \
  --slot-id 1
```

### 2. Chỉ chạy luồng thành công

```bash
python3 backend/scripts/manual_payment_test_suite.py \
  --mode success \
  --base-url http://localhost:5000 \
  --product-id 1 \
  --price 10000 \
  --slot-id 1
```

### 3. Chỉ chạy luồng lỗi

```bash
python3 backend/scripts/manual_payment_test_suite.py \
  --mode negative \
  --base-url http://localhost:5000 \
  --product-id 1 \
  --price 10000 \
  --slot-id 1
```

### 4. Test cả bước nhả hàng

```bash
python3 backend/scripts/manual_payment_test_suite.py \
  --mode success \
  --base-url http://localhost:5000 \
  --product-id 1 \
  --price 10000 \
  --slot-id 1 \
  --machine-key may1 \
  --slot-code A1 \
  --complete-dispense
```

### 5. Test nhánh hủy trong success mode

```bash
python3 backend/scripts/manual_payment_test_suite.py \
  --mode success \
  --base-url http://localhost:5000 \
  --product-id 1 \
  --price 10000 \
  --slot-id 1 \
  --test-cancel
```

## Tham số chính

- `--base-url`
  URL backend, mặc định `http://localhost:5000`

- `--product-id`
  ID sản phẩm dùng để tạo order test

- `--price`
  Giá dự kiến của order test

- `--slot-id`
  `slot_id` gắn vào pending order khi tạo

- `--machine-key`
  Dùng khi gọi API IoT như `/api/iot/pending-orders`

- `--slot-code`
  Dùng khi gọi `/api/iot/dispense-complete`

- `--complete-dispense`
  Bật bước xác nhận đã nhả hàng

- `--test-cancel`
  Chỉ dùng trong `success mode`, chạy nhánh hủy thay vì nhánh thanh toán thành công

## Kết quả mong đợi

- Nếu test pass, script sẽ in `completed successfully`
- Nếu test fail, script sẽ dừng ngay tại bước lỗi và in `TEST FAILED`

## Ghi chú

- Các script này là manual integration scripts, chưa phải test tự động kiểu `pytest`
- Mỗi lần chạy sẽ tạo order mới trong DB
- Khi chạy nhiều lần, nên theo dõi thêm `/api/debug-db` hoặc DB trực tiếp để đối chiếu
