# Database Tables and Columns

This document outlines all database tables defined in the backend `app/models` directory, along with each table's columns and relevant enums or relationships.

---

## `users`
- `id` – Integer, PK, index
- `username` – String, unique, index
- `email` – String, unique, index, nullable
- `hashed_password` – String
- `full_name` – String, nullable
- `role` – Enum(`UserRole`): `ADMIN` or `STAFF` (default STAFF)
- `is_active` – Boolean, default `True`

## `machines`
- `id` – Integer, PK, index
- `name` – String, unique, index
- `location` – String
- `status` – String (default `ONLINE`; enum `MachineStatus` includes `ONLINE`, `OFFLINE`, `MAINTENANCE`, `ERROR`)
- `secret_key` – String, unique
- `last_ping` – DateTime(tz), server_default `now()`, onupdate `now()`

**Relationships:**
- `slots` ↔ `Slot`
- `orders` ↔ `Order`

## `slots`
- `id` – Integer, PK, index
- `machine_id` – Integer, FK → `machines.id`
- `slot_code` – String (e.g. A1, B2, ...)
- `product_id` – Integer, FK → `products.id`
- `stock` – Integer, default 0
- `capacity` – Integer, default 10

**Relationships:**
- `machine` ↔ `Machine`
- `product` ↔ `Product`

## `products`
- `id` – Integer, PK, index
- `name` – String, index
- `price` – Integer
- `image_url` – String
- `description` – Text, nullable
- `category` – String, default `"drink"`
- `is_available` – Boolean, default `True`

**Relationships:**
- `slots` ↔ `Slot`

## `orders`
- `id` – Integer, PK, index
- `order_code` – BigInteger, unique, index
- `product_id` – Integer, FK → `products.id`
- `machine_id` – Integer, FK → `machines.id`, nullable
- `amount` – Integer
- `status` – String (enum `OrderStatus`: `PENDING`, `PAID`, `DISPENSING`, `COMPLETED`, `FAILED`, `CANCELLED`; default `PENDING`)
- `payment_url` – String, nullable
- `qr_code` – String, nullable
- `created_at` – DateTime(tz), server_default `now()`
- `updated_at` – DateTime(tz), onupdate `now()`

**Relationships:**
- `product` ↔ `Product`
- `machine` ↔ `Machine`

## `refill_logs`
- `id` – Integer, PK, index
- `user_id` – Integer, FK → `users.id`
- `machine_id` – Integer, FK → `machines.id`
- `slot_id` – Integer, FK → `slots.id`
- `product_id` – Integer, FK → `products.id`
- `quantity` – Integer, not nullable – số lượng nạp thêm
- `old_quantity` – Integer, not nullable – trước khi nạp
- `new_quantity` – Integer, not nullable – sau khi nạp
- `timestamp` – DateTime(tz), server_default `now()`

**Relationships:**
- `user`, `machine`, `slot`, `product`

## `issues`
- `id` – Integer, PK, index
- `user_id` – Integer, FK → `users.id`
- `machine_id` – Integer, FK → `machines.id`, nullable
- `content` – String, not nullable
- `status` – String (enum `IssueStatus`: `OPEN`, `IN_PROGRESS`, `RESOLVED`, `CLOSED`; default `OPEN`)
- `created_at` – DateTime(tz), server_default `now()`
- `updated_at` – DateTime(tz), onupdate `now()`

**Relationships:**
- `user`, `machine`

## `system_settings`
- `key` – String, PK, index
- `value` – Text, nullable
- `type` – String, default `"string"` (can be `number`, `boolean`, `json`)
- `description` – String, nullable
- `group` – String, default `"general"`
