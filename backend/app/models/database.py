from datetime import datetime
from app import db

class User(db.Model):
    __tablename__ = 'users'
    
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    create_at = db.Column(db.DateTime, default=datetime.utcnow)

class Product(db.Model):
    __tablename__ = 'products'
    
    product_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    image = db.Column(db.String(500), nullable=True)
    active = db.Column(db.Boolean, default=True)

class Slot(db.Model):
    __tablename__ = 'slots'
    
    slot_id = db.Column(db.Integer, primary_key=True)
    machine_id = db.Column(db.Integer, db.ForeignKey('machines.machine_id'), nullable=False)
    slot_code = db.Column(db.String(10), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.product_id'), nullable=True)
    stock = db.Column(db.Integer, default=0)
    capacity = db.Column(db.Integer, default=10)
    
    machine = db.relationship('Machine', backref='slots')
    product = db.relationship('Product', backref='slots')

class Machine(db.Model):
    __tablename__ = 'machines'
    
    machine_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(200), nullable=True)
    status = db.Column(db.String(20), default='active')
    secret_key = db.Column(db.String(200), nullable=True)

class Order(db.Model):
    __tablename__ = 'orders'
    
    order_id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.product_id'), nullable=False)
    price_snapshot = db.Column(db.Float, nullable=False)  # Giá tại thời điểm đặt hàng
    slot_id = db.Column(db.Integer, db.ForeignKey('slots.slot_id'), nullable=False)
    status = db.Column(db.String(20), default='pending')
    create_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    product = db.relationship('Product', backref='orders')
    slot = db.relationship('Slot', backref='orders')

class Transaction(db.Model):
    __tablename__ = 'transactions'
    
    transaction_id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.order_id'), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    bank_trans_id = db.Column(db.String(100), nullable=True)  # Mã giao dịch ngân hàng
    description = db.Column(db.Text, nullable=True)
    sender_account = db.Column(db.String(50), nullable=True)
    sender_bank = db.Column(db.String(50), nullable=True)
    status = db.Column(db.String(50), default='pending')
    
    order = db.relationship('Order', backref='transactions')