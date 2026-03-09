"""
Helper function để ghi log thao tác quản trị web.
Fail-safe: nếu ghi log lỗi sẽ không ảnh hưởng đến request chính.
"""
from flask import request


def log_admin_action(user_id, action, detail=None, target_type=None, target_id=None):
    """
    Ghi log thao tác quản trị vào bảng admin_activity_logs.
    
    Args:
        user_id: ID nhân viên thực hiện (None nếu chưa xác thực, VD: login_failed)
        action: Loại hành động (login, create_product, update_slot, ...)
        detail: Mô tả chi tiết (VD: "Tạo sản phẩm 'Coca' giá 10000đ")
        target_type: Loại đối tượng bị tác động (product, slot, machine, user, order)
        target_id: ID đối tượng bị tác động
    """
    try:
        from app.models import AdminActivityLog
        from app import db

        ip = request.remote_addr if request else None

        log_entry = AdminActivityLog(
            user_id=user_id,
            action=action,
            detail=detail,
            target_type=target_type,
            target_id=target_id,
            ip_address=ip
        )
        db.session.add(log_entry)
        db.session.commit()
    except Exception as e:
        # Fail-safe: không để lỗi log ảnh hưởng request chính
        print(f"⚠️ Admin log error: {e}")
        try:
            from app import db
            db.session.rollback()
        except Exception:
            pass
