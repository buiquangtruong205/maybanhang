from datetime import datetime
from app import db


# -----------------------
# Base timestamp mixin
# -----------------------
class TimestampMixin:
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)


# =======================
# 1) Quản trị
# =======================
class User(db.Model, TimestampMixin):
    __tablename__ = "users"

    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password = db.Column(db.String(200), nullable=False)  # khuyến nghị: password_hash
    is_active = db.Column(db.Boolean, default=True, nullable=False)


# =======================
# 2) Thiết bị IoT
# =======================
class Machine(db.Model, TimestampMixin):
    __tablename__ = "machines"

    machine_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    location = db.Column(db.String(200), nullable=True)
    status = db.Column(db.String(20), default="active", nullable=False, index=True)
    secret_key = db.Column(db.String(200), nullable=True)  # khuyến nghị: secret_key_hash

    # relationships
    slots = db.relationship("Slot", backref="machine", lazy=True)


# =======================
# 3) Sản phẩm & Kho
# =======================
class Product(db.Model, TimestampMixin):
    __tablename__ = "products"

    product_id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(100), nullable=False, index=True)
    price = db.Column(db.Numeric(10, 2), nullable=False)  # dùng Numeric thay vì Float
    image = db.Column(db.String(500), nullable=True)
    active = db.Column(db.Boolean, default=True, nullable=False, index=True)


class Slot(db.Model, TimestampMixin):
    __tablename__ = "slots"

    slot_id = db.Column(db.Integer, primary_key=True)
    machine_id = db.Column(db.Integer, db.ForeignKey("machines.machine_id"), nullable=False, index=True)
    slot_code = db.Column(db.String(10), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.product_id"), nullable=True, index=True)
    stock = db.Column(db.Integer, default=0, nullable=False)
    capacity = db.Column(db.Integer, default=10, nullable=False)

    product = db.relationship("Product", backref="slots")

    __table_args__ = (
        db.UniqueConstraint("machine_id", "slot_code", name="uq_slots_machine_slotcode"),
        db.Index("ix_slots_machine_product", "machine_id", "product_id"),
    )


# =======================
# 4) Bán hàng & Thanh toán
# =======================
class Order(db.Model, TimestampMixin):
    __tablename__ = "orders"

    order_id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.product_id"), nullable=False, index=True)
    slot_id = db.Column(db.Integer, db.ForeignKey("slots.slot_id"), nullable=True, index=True)  # nullable for demo without slots

    price_snapshot = db.Column(db.Numeric(10, 2), nullable=False)

    # tách trạng thái
    status_payment = db.Column(db.String(20), default="pending", nullable=False, index=True)
    status_slots = db.Column(db.String(20), default="pending", nullable=False, index=True)

    product = db.relationship("Product", backref="orders")
    slot = db.relationship("Slot", backref="orders")

    __table_args__ = (
        db.Index("ix_orders_status", "status_payment", "status_slots"),
    )


class Transaction(db.Model, TimestampMixin):
    __tablename__ = "transactions"

    transaction_id = db.Column(db.Integer, primary_key=True)

    order_id = db.Column(db.Integer, db.ForeignKey("orders.order_id"), nullable=False, index=True)
    amount = db.Column(db.Numeric(10, 2), nullable=False)

    bank_trans_id = db.Column(db.String(100), nullable=True, index=True)  # mã giao dịch ngân hàng/ví
    description = db.Column(db.Text, nullable=True)

    sender_account = db.Column(db.String(50), nullable=True)
    sender_bank = db.Column(db.String(50), nullable=True)

    status = db.Column(db.String(50), default="pending", nullable=False, index=True)

    order = db.relationship("Order", backref="transactions")

    __table_args__ = (
        db.Index("ix_transactions_order_status", "order_id", "status"),
    )


class PaymentCallback(db.Model):
    """
    Bảng integrity cho callback thanh toán (khuyến nghị dùng để đối soát).
    """
    __tablename__ = "payment_callbacks"

    callback_id = db.Column(db.BigInteger, primary_key=True)
    bank_trans_id = db.Column(db.String(100), nullable=True, index=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.order_id"), nullable=True, index=True)

    payload_raw = db.Column(db.JSON, nullable=True)  # nếu DB không hỗ trợ JSON -> đổi Text
    payload_hash = db.Column(db.String(128), nullable=True, index=True)
    signature_ok = db.Column(db.Boolean, default=False, nullable=False, index=True)

    received_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    ip_source = db.Column(db.String(45), nullable=True)

    order = db.relationship("Order", backref="payment_callbacks")





# =======================
# 6) Bảo mật IoT - Identity / Session / Rotation
# =======================
class DeviceIdentity(db.Model):
    __tablename__ = "device_identity"

    machine_id = db.Column(db.Integer, db.ForeignKey("machines.machine_id"), primary_key=True)

    device_public_key = db.Column(db.Text, nullable=True)
    cert_fingerprint = db.Column(db.String(128), nullable=True, index=True)
    secure_element_id = db.Column(db.String(100), nullable=True, index=True)
    mac_address = db.Column(db.String(32), nullable=True, index=True)

    provisioned_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    revoked_at = db.Column(db.DateTime, nullable=True, index=True)

    status = db.Column(db.String(20), default="active", nullable=False, index=True)  # active/revoked

    machine = db.relationship("Machine", backref=db.backref("device_identity", uselist=False))


class DeviceSession(db.Model):
    __tablename__ = "device_sessions"

    session_id = db.Column(db.Integer, primary_key=True)
    machine_id = db.Column(db.Integer, db.ForeignKey("machines.machine_id"), nullable=False, index=True)

    token_hash = db.Column(db.String(255), unique=True, nullable=False, index=True)
    issued_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    expires_at = db.Column(db.DateTime, nullable=False, index=True)

    last_seen_at = db.Column(db.DateTime, nullable=True, index=True)
    ip_address = db.Column(db.String(45), nullable=True)

    is_revoked = db.Column(db.Boolean, default=False, nullable=False, index=True)

    machine = db.relationship("Machine", backref="device_sessions")






class ApiAuditLog(db.Model):
    __tablename__ = "api_audit_logs"

    request_id = db.Column(db.BigInteger, primary_key=True)
    machine_id = db.Column(db.Integer, db.ForeignKey("machines.machine_id"), nullable=True, index=True)

    endpoint = db.Column(db.String(200), nullable=False, index=True)
    method = db.Column(db.String(10), nullable=False)
    ip_address = db.Column(db.String(45), nullable=True, index=True)

    response_code = db.Column(db.Integer, nullable=False, index=True)
    payload_hash = db.Column(db.String(128), nullable=True, index=True)
    signature_ok = db.Column(db.Boolean, default=False, nullable=False, index=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    machine = db.relationship("Machine", backref="api_audit_logs")


class StaffAccessLog(db.Model):
    __tablename__ = "staff_access_logs"

    access_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=True, index=True)
    machine_id = db.Column(db.Integer, db.ForeignKey("machines.machine_id"), nullable=False, index=True)

    action = db.Column(db.String(30), nullable=False, index=True)  # open/close/refill/maintenance
    started_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    ended_at = db.Column(db.DateTime, nullable=True, index=True)
    note = db.Column(db.Text, nullable=True)

    user = db.relationship("User", backref="access_logs")
    machine = db.relationship("Machine", backref="access_logs")



# =======================
# 9) WebAuthn / Passkey
# =======================
class WebAuthnCredential(db.Model, TimestampMixin):
    """
    Lưu trữ Passkey/WebAuthn credentials.
    Mỗi user chỉ được phép có 1 credential (1 passkey).
    
    LƯU Ý: Nếu user bật sync passkey (iCloud Keychain / Google Password Manager),
    passkey có thể sync sang thiết bị khác. Đây là "1 credential" không phải "1 thiết bị vật lý".
    """
    __tablename__ = "webauthn_credentials"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), unique=True, nullable=False, index=True)
    
    # Credential data từ WebAuthn
    credential_id = db.Column(db.LargeBinary, unique=True, nullable=False)
    public_key = db.Column(db.LargeBinary, nullable=False)
    sign_count = db.Column(db.Integer, default=0, nullable=False)
    
    # Transports - để browser biết cách giao tiếp với authenticator
    transports = db.Column(db.String(200), nullable=True)  # JSON array: ["internal", "hybrid", "usb", ...]
    
    # Thông tin thiết bị
    aaguid = db.Column(db.String(36), nullable=True)  # Authenticator model identifier
    device_name = db.Column(db.String(100), nullable=True)  # Human-readable device name
    
    # Audit fields
    last_used_at = db.Column(db.DateTime, nullable=True, index=True)  # Lần cuối đăng nhập bằng passkey
    
    user = db.relationship("User", backref=db.backref("webauthn_credential", uselist=False))