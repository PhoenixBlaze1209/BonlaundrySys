# services/audit_service.py
"""
Audit Logging Service for Bon Laundry Station.
Tracks operational activities and administrative adjustments performed by staff and managers.
"""

import logging
from datetime import datetime
from flask import session, request, has_request_context
from config.database import SessionLocal
from models.schemas import AuditLog

logger = logging.getLogger(__name__)


class AuditAction:
    ORDER_VERIFIED       = 'ORDER_VERIFIED'
    ORDER_ALTERED        = 'ORDER_ALTERED'
    QUEUE_ADVANCED       = 'QUEUE_ADVANCED'
    APPOINTMENT_CHECKIN  = 'APPOINTMENT_CHECKIN'
    APPOINTMENT_COMPLETED= 'APPOINTMENT_COMPLETED'
    APPOINTMENT_CANCELLED= 'APPOINTMENT_CANCELLED'
    PAYMENT_UPDATED      = 'PAYMENT_UPDATED'
    FULFILLMENT_UPDATED  = 'FULFILLMENT_UPDATED'
    MACHINE_STATE_CHANGED= 'MACHINE_STATE_CHANGED'
    MACHINE_PRICE_UPDATED= 'MACHINE_PRICE_UPDATED'
    USER_PROVISIONED     = 'USER_PROVISIONED'
    USER_ROLE_CHANGED    = 'USER_ROLE_CHANGED'
    ROLE_VIEW_SWITCHED   = 'ROLE_VIEW_SWITCHED'
    USER_LOGIN           = 'USER_LOGIN'


class AuditService:
    @staticmethod
    def log(action: str, entity_type: str = None, entity_id: str = None,
            details: str = None, user_id: int = None, user_name: str = None,
            user_email: str = None, user_role: str = None, ip_address: str = None):
        """
        Records an audit log entry.
        Automatically resolves actor metadata from the active Flask session/request if omitted.
        Guaranteed non-blocking: never raises an exception to the caller.
        """
        try:
            if has_request_context():
                if user_id is None:
                    user_id = session.get('user_id')
                if user_name is None:
                    user_name = session.get('user_name')
                if user_email is None:
                    user_email = session.get('user_email')
                if user_role is None:
                    user_role = session.get('user_role')
                if ip_address is None:
                    # Capture forwarded-for if behind reverse proxy
                    ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
                    if ip_address and ',' in ip_address:
                        ip_address = ip_address.split(',')[0].strip()

            db = SessionLocal()
            try:
                entry = AuditLog(
                    user_id=user_id,
                    user_name=user_name,
                    user_email=user_email,
                    user_role=user_role,
                    action=action,
                    entity_type=entity_type,
                    entity_id=str(entity_id) if entity_id is not None else None,
                    details=details[:500] if details else None,
                    ip_address=ip_address[:45] if ip_address else None,
                    created_at=datetime.utcnow()
                )
                db.add(entry)
                try:
                    db.commit()
                except Exception:
                    db.rollback()
                    # If user_id violates foreign key (e.g. mock test user), retry with user_id=None
                    entry.user_id = None
                    db.add(entry)
                    db.commit()
            finally:
                db.close()
        except Exception as e:
            logger.error(f"AuditService.log error: {e}", exc_info=True)

    @staticmethod
    def get_logs(page: int = 1, limit: int = 20, staff_id: int = None,
                 action: str = None, search: str = None):
        """
        Retrieves paginated audit logs with optional filters for the Manager/Super Admin dashboard.
        """
        db = SessionLocal()
        try:
            query = db.query(AuditLog)

            if staff_id:
                query = query.filter(AuditLog.user_id == staff_id)

            if action and action != 'ALL':
                query = query.filter(AuditLog.action == action)

            if search:
                term = f"%{search.strip()}%"
                query = query.filter(
                    (AuditLog.details.ilike(term)) |
                    (AuditLog.user_name.ilike(term)) |
                    (AuditLog.user_email.ilike(term)) |
                    (AuditLog.entity_id.ilike(term))
                )

            total = query.count()
            pages = max(1, (total + limit - 1) // limit)
            page = max(1, min(page, pages))

            records = query.order_by(AuditLog.created_at.desc()).offset((page - 1) * limit).limit(limit).all()

            # Live summary counters
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            today_count = db.query(AuditLog).filter(AuditLog.created_at >= today_start).count()
            order_actions = db.query(AuditLog).filter(
                AuditLog.created_at >= today_start,
                AuditLog.action.in_([AuditAction.ORDER_VERIFIED, AuditAction.QUEUE_ADVANCED, AuditAction.APPOINTMENT_COMPLETED])
            ).count()
            machine_actions = db.query(AuditLog).filter(
                AuditLog.created_at >= today_start,
                AuditLog.action.in_([AuditAction.MACHINE_STATE_CHANGED, AuditAction.MACHINE_PRICE_UPDATED])
            ).count()

            return {
                'logs': [{
                    'log_id': r.log_id,
                    'user_id': r.user_id,
                    'user_name': r.user_name or 'System',
                    'user_email': r.user_email or '—',
                    'user_role': r.user_role or 'System',
                    'action': r.action,
                    'entity_type': r.entity_type,
                    'entity_id': r.entity_id,
                    'details': r.details,
                    'ip_address': r.ip_address,
                    'created_at': r.created_at.strftime('%Y-%m-%d %H:%M:%S') if r.created_at else ''
                } for r in records],
                'pagination': {
                    'total': total,
                    'page': page,
                    'pages': pages,
                    'limit': limit
                },
                'summary': {
                    'today_total': today_count,
                    'today_orders': order_actions,
                    'today_machines': machine_actions
                }
            }
        finally:
            db.close()
