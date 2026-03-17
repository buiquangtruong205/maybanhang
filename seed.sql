INSERT INTO machines (machine_id, name, location, status, secret_key, created_at)
VALUES (3, 'Máy Bán Hàng Thử Nghiệm', 'Phòng kỹ thuật', 'active', 'maybanhang-v3', NOW())
ON CONFLICT (machine_id) DO NOTHING;

INSERT INTO products (product_id, product_name, price, image, active, created_at)
VALUES
(1, 'Coca Cola', 10000, 'https://cdn.tgdd.vn/Products/Images/2565/69106/bhx/nuoc-ngot-coca-cola-vi-nguyen-ban-original-taste-320ml-202302251310115049.jpeg', true, NOW()),
(2, 'Pepsi', 10000, 'https://cdn.tgdd.vn/Products/Images/2565/69107/bhx/nuoc-ngot-pepsi-cola-320mll-202212301416568461.jpg', true, NOW()),
(3, 'Nước Suối Aquafina', 5000, 'https://cdn.tgdd.vn/Products/Images/3141/76366/bhx/nuoc-tinh-khiet-aquafina-500ml-202206161426477150.jpg', true, NOW()),
(4, 'Bò Húc (Red Bull)', 15000, 'https://cdn.tgdd.vn/Products/Images/2565/76082/bhx/nuoc-tang-luc-red-bull-250ml-202212231450011516.jpg', true, NOW()),
(5, 'Trà Ô Long TEA+', 12000, 'https://m.media-amazon.com/images/I/61U4eE8MbtL._AC_UF1000,1000_QL80_.jpg', true, NOW()),
(6, 'Snack O-Star', 15000, 'https://cdn.tgdd.vn/Products/Images/3364/110756/bhx/snack-khoai-tay-vi-tu-nhien-ostar-combo-2-goi-x-122g-202212151523315752.jpg', true, NOW())
ON CONFLICT (product_id) DO NOTHING;

INSERT INTO slots (machine_id, slot_code, product_id, stock, capacity, created_at)
VALUES
(3, 'A1', 1, 10, 10, NOW()),
(3, 'A2', 2, 8, 10, NOW()),
(3, 'A3', 3, 15, 20, NOW()),
(3, 'B1', 4, 5, 10, NOW()),
(3, 'B2', 5, 12, 15, NOW()),
(3, 'B3', 6, 7, 10, NOW())
ON CONFLICT DO NOTHING;

SELECT setval('products_product_id_seq', (SELECT MAX(product_id) FROM products));
SELECT setval('slots_slot_id_seq', (SELECT MAX(slot_id) FROM slots));
