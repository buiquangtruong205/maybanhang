"""
Security Log Routes
- GET  /api/audit-logs          — Xem lịch sử request API (ApiAuditLog)
- GET  /api/staff-access        — Xem lịch sử nhân viên mở máy
- POST /api/staff-access        — Ghi nhận nhân viên bắt đầu mở máy
- PUT  /api/staff-access/<id>/close  — Ghi nhận nhân viên đóng máy (kết thúc)
- GET  /api/staff-access/<id>   — Xem chi tiết 1 log
"""
from flask import Blueprint, request, jsonify
from datetime import datetime
from pydantic import ValidationError
from app import db
from app.models import ApiAuditLog, StaffAccessLog
from app.schemas import (
    ApiAuditLogOut,
    StaffAccessLogCreate, StaffAccessLogOut, StaffAccessLogEnd
)
from app.utils import token_required

security_bp = Blueprint('security', __name__)


# ==================== ApiAuditLog ====================

@security_bp.route('/audit-logs', methods=['GET'])
@token_required
def get_audit_logs(current_user):
    """
    Lấy danh sách lịch sử request API (có phân trang + filter).

    Query params:
        page        — Trang (default 1)
        per_page    — Số bản ghi mỗi trang (default 50, max 200)
        machine_id  — Lọc theo máy
        endpoint    — Lọc theo endpoint (partial match)
        method      — Lọc theo HTTP method (GET, POST, ...)
        status_code — Lọc theo response code
        sig_ok      — Lọc signature_ok (true/false)
    """
    page        = request.args.get('page', 1, type=int)
    per_page    = min(request.args.get('per_page', 50, type=int), 200)
    machine_id  = request.args.get('machine_id', type=int)
    endpoint    = request.args.get('endpoint', type=str)
    method      = request.args.get('method', type=str)
    status_code = request.args.get('status_code', type=int)
    sig_ok      = request.args.get('sig_ok', type=str)

    query = ApiAuditLog.query

    if machine_id:
        query = query.filter(ApiAuditLog.machine_id == machine_id)
    if endpoint:
        query = query.filter(ApiAuditLog.endpoint.ilike(f'%{endpoint}%'))
    if method:
        query = query.filter(ApiAuditLog.method == method.upper())
    if status_code:
        query = query.filter(ApiAuditLog.response_code == status_code)
    if sig_ok is not None:
        query = query.filter(ApiAuditLog.signature_ok == (sig_ok.lower() == 'true'))

    pagination = query.order_by(ApiAuditLog.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    data = [ApiAuditLogOut.model_validate(log).model_dump() for log in pagination.items]

    return jsonify({
        'success': True,
        'message': f'Found {pagination.total} audit log(s)',
        'data': data,
        'meta': {
            'page': page,
            'per_page': per_page,
            'total': pagination.total,
            'pages': pagination.pages
        }
    })


@security_bp.route('/audit-logs/stats', methods=['GET'])
@token_required
def get_audit_stats(current_user):
    """
    Tóm tắt nhanh ApiAuditLog: tổng request, tỉ lệ lỗi, chữ ký không hợp lệ.
    """
    from sqlalchemy import func

    total = db.session.query(func.count(ApiAuditLog.request_id)).scalar() or 0
    errors = db.session.query(func.count(ApiAuditLog.request_id))\
        .filter(ApiAuditLog.response_code >= 400).scalar() or 0
    bad_sig = db.session.query(func.count(ApiAuditLog.request_id))\
        .filter(ApiAuditLog.signature_ok == False).scalar() or 0

    return jsonify({
        'success': True,
        'data': {
            'total_requests': total,
            'error_requests': errors,
            'bad_signature_requests': bad_sig,
            'error_rate_pct': round(errors / total * 100, 2) if total else 0
        }
    })


# ==================== StaffAccessLog ====================

@security_bp.route('/staff-access', methods=['GET'])
@token_required
def get_staff_access_logs(current_user):
    """
    Lấy danh sách lịch sử nhân viên mở/vận hành máy.

    Query params:
        page       — Trang (default 1)
        per_page   — Số bản ghi mỗi trang (default 50, max 200)
        machine_id — Lọc theo máy
        user_id    — Lọc theo nhân viên
        action     — Lọc theo loại hành động (open/close/refill/maintenance)
        open_only  — Nếu true, chỉ lấy các phiên chưa đóng (ended_at IS NULL)
    """
    page       = request.args.get('page', 1, type=int)
    per_page   = min(request.args.get('per_page', 50, type=int), 200)
    machine_id = request.args.get('machine_id', type=int)
    user_id    = request.args.get('user_id', type=int)
    action     = request.args.get('action', type=str)
    open_only  = request.args.get('open_only', 'false').lower() == 'true'

    query = StaffAccessLog.query

    if machine_id:
        query = query.filter(StaffAccessLog.machine_id == machine_id)
    if user_id:
        query = query.filter(StaffAccessLog.user_id == user_id)
    if action:
        query = query.filter(StaffAccessLog.action == action.lower())
    if open_only:
        query = query.filter(StaffAccessLog.ended_at == None)

    pagination = query.order_by(StaffAccessLog.started_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    data = [StaffAccessLogOut.model_validate(log).model_dump() for log in pagination.items]

    return jsonify({
        'success': True,
        'message': f'Found {pagination.total} access log(s)',
        'data': data,
        'meta': {
            'page': page,
            'per_page': per_page,
            'total': pagination.total,
            'pages': pagination.pages
        }
    })


@security_bp.route('/staff-access/<int:access_id>', methods=['GET'])
@token_required
def get_staff_access_log(current_user, access_id):
    """Xem chi tiết 1 staff access log"""
    log = StaffAccessLog.query.get_or_404(access_id)
    return jsonify({
        'success': True,
        'message': 'Staff access log retrieved',
        'data': StaffAccessLogOut.model_validate(log).model_dump()
    })


@security_bp.route('/staff-access', methods=['POST'])
@token_required
def create_staff_access_log(current_user):
    """
    Ghi nhận nhân viên bắt đầu mở/vận hành máy.

    Body:
        machine_id  — ID máy (bắt buộc)
        action      — Loại hành động: open / refill / maintenance (bắt buộc)
        note        — Ghi chú (tuỳ chọn)
        user_id     — ID nhân viên (tuỳ chọn, mặc định là current_user)
    """
    try:
        json_data = request.get_json(force=True, silent=True)
        if not json_data:
            return jsonify({'success': False, 'message': 'Request body must be valid JSON'}), 400

        # Mặc định user_id là người đang đăng nhập nếu không truyền
        if 'user_id' not in json_data:
            json_data['user_id'] = current_user.user_id

        data = StaffAccessLogCreate(**json_data)

        # Kiểm tra action hợp lệ
        valid_actions = {'open', 'close', 'refill', 'maintenance'}
        if data.action not in valid_actions:
            return jsonify({
                'success': False,
                'message': f'action phải là một trong: {", ".join(valid_actions)}'
            }), 400

        new_log = StaffAccessLog(
            user_id=data.user_id,
            machine_id=data.machine_id,
            action=data.action,
            note=data.note,
            started_at=datetime.utcnow()
        )

        db.session.add(new_log)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'Đã ghi nhận hành động "{data.action}" cho máy {data.machine_id}',
            'data': StaffAccessLogOut.model_validate(new_log).model_dump()
        }), 201

    except ValidationError as e:
        return jsonify({'success': False, 'message': 'Validation error', 'errors': e.errors()}), 422
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@security_bp.route('/staff-access/<int:access_id>/close', methods=['PUT'])
@token_required
def close_staff_access_log(current_user, access_id):
    """
    Đóng phiên làm việc (ghi nhận nhân viên đã xong việc).

    Body (optional):
        note — Ghi chú khi kết thúc
    """
    try:
        log = StaffAccessLog.query.get_or_404(access_id)

        if log.ended_at is not None:
            return jsonify({
                'success': False,
                'message': 'Phiên này đã được đóng trước đó',
                'ended_at': log.ended_at.isoformat()
            }), 409

        json_data = request.get_json(force=True, silent=True) or {}
        data = StaffAccessLogEnd(**json_data)

        log.ended_at = datetime.utcnow()
        if data.note:
            # Append thêm note đóng vào note gốc nếu có
            existing_note = log.note or ''
            log.note = f"{existing_note}\n[Đóng]: {data.note}".strip() if existing_note else f"[Đóng]: {data.note}"

        db.session.commit()

        duration_mins = round((log.ended_at - log.started_at).total_seconds() / 60, 1)

        return jsonify({
            'success': True,
            'message': f'Đã đóng phiên sau {duration_mins} phút',
            'data': StaffAccessLogOut.model_validate(log).model_dump()
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
