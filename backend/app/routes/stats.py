from flask import Blueprint, jsonify
from sqlalchemy import func, desc
from datetime import datetime
from app import db
from app.models import Order, Transaction, Product
from app.utils import token_required

stats_bp = Blueprint('stats', __name__)

@stats_bp.route('/stats', methods=['GET'])
@token_required
def get_stats(current_user):
    # Lấy tháng hiện tại
    now = datetime.utcnow()
    start_of_month = datetime(now.year, now.month, 1)
    
    # 1. Doanh thu (tổng giá trị các đơn hàng thành công)
    monthly_revenue = db.session.query(
        func.sum(Order.price_snapshot)
    ).filter(
        Order.status_payment == 'completed'
    ).scalar() or 0
    
    # 2. Sản phẩm bán chạy nhất (dựa vào orders)
    best_selling = db.session.query(
        Product.product_id,
        Product.product_name,
        func.count(Order.order_id).label('total_sold')
    ).join(Order, Order.product_id == Product.product_id)\
    .filter(Order.status_payment == 'completed')\
    .group_by(Product.product_id, Product.product_name)\
    .order_by(desc('total_sold'))\
    .first()
    
    best_product = {
        'product_id': best_selling[0] if best_selling else None,
        'product_name': best_selling[1] if best_selling else 'Chưa có',
        'total_sold': best_selling[2] if best_selling else 0
    }
    
    # 3. Người mua nhiều nhất (ngân hàng có nhiều giao dịch nhất)
    top_buyer = db.session.query(
        Transaction.sender_bank,
        Transaction.sender_account,
        func.count(Transaction.transaction_id).label('transaction_count'),
        func.sum(Transaction.amount).label('total_amount')
    ).filter(
        Transaction.status == 'completed',
        Transaction.sender_bank.isnot(None)
    ).group_by(Transaction.sender_bank, Transaction.sender_account)\
    .order_by(desc('transaction_count'))\
    .first()
    
    top_customer = {
        'sender_bank': top_buyer[0] if top_buyer else 'Chưa có',
        'sender_account': top_buyer[1] if top_buyer else None,
        'transaction_count': top_buyer[2] if top_buyer else 0,
        'total_amount': float(top_buyer[3]) if top_buyer and top_buyer[3] else 0
    }
    
    # 4. Tổng đơn hàng tháng này
    total_orders = db.session.query(
        func.count(Order.order_id)
    ).filter(Order.status_payment == 'completed').scalar() or 0
    
    return jsonify({
        'success': True,
        'message': 'Statistics retrieved successfully',
        'data': {
            'monthly_revenue': float(monthly_revenue),
            'best_product': best_product,
            'top_customer': top_customer,
            'total_orders': total_orders
        }
    })
