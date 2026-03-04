<<<<<<< HEAD
from app.models.user import User, UserRole
from app.models.machine import Machine, MachineStatus
from app.models.product import Product
from app.models.slot import Slot
from app.models.order import Order
from app.models.issue import Issue, IssueStatus
from app.models.log import RefillLog
from app.models.setting import SystemSetting
=======
from app.models.database import (
    User, Product, Slot, Order, Machine, Transaction,
    PaymentCallback, CashDeposit,
    DeviceIdentity, DeviceSession,
    ApiAuditLog, StaffAccessLog,
    WebAuthnCredential,
    DeviceLog, FirmwareUpdate
)

__all__ = [
    'User', 'Product', 'Slot', 'Order', 'Machine', 'Transaction',
    'PaymentCallback', 'CashDeposit',
    'DeviceIdentity', 'DeviceSession',
    'ApiAuditLog', 'StaffAccessLog',
    'WebAuthnCredential',
    'DeviceLog', 'FirmwareUpdate'
]


>>>>>>> origin/API_WEB_SERVER
