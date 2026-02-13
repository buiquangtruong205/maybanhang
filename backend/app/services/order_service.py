from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.order import Order, OrderStatus
from app.utils.helpers import generate_order_code
from app.core.socket_manager import broadcast_order_update

class OrderService:
    @staticmethod
    async def create_new_order(db: AsyncSession, product_id: int, machine_id: int, amount: int):
        """Khởi tạo đơn hàng mới với mã PayOS integer."""
        new_order = Order(
            order_code=generate_order_code(),
            product_id=product_id,
            machine_id=machine_id,
            amount=amount,
            status=OrderStatus.PENDING
        )
        db.add(new_order)
        await db.commit()
        await db.refresh(new_order)
        
        # Real-time notify
        await broadcast_order_update(new_order.to_dict() if hasattr(new_order, 'to_dict') else {
            "id": new_order.id,
            "order_code": new_order.order_code,
            "status": new_order.status,
            "amount": new_order.amount
        })
        
        return new_order

    @staticmethod
    async def get_order_by_code(db: AsyncSession, order_code: int):
        """Tìm đơn hàng theo mã code (thường dùng cho IoT check)."""
        result = await db.execute(select(Order).where(Order.order_code == order_code))
        return result.scalar_one_or_none()

    @staticmethod
    async def update_status(db: AsyncSession, order_id: int, status: OrderStatus):
        """Cập nhật trạng thái đơn hàng."""
        result = await db.execute(select(Order).where(Order.id == order_id))
        order = result.scalar_one_or_none()
        if order:
            order.status = status
            await db.commit()
            
            # Real-time notify
            await broadcast_order_update({
                "id": order.id,
                "order_code": order.order_code,
                "status": order.status,
                "amount": order.amount
            })
            
            return order
        return None

    @staticmethod
    async def list_orders(db: AsyncSession, skip: int = 0, limit: int = 50, status: str = None):
        """Liệt kê danh sách đơn hàng có phân trang và lọc theo trạng thái."""
        query = select(Order).order_by(Order.created_at.desc())
        if status:
            query = query.where(Order.status == status)
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def manual_confirm(db: AsyncSession, order_code: int):
        """Xác nhận đơn hàng thủ công bởi nhân viên."""
        order = await OrderService.get_order_by_code(db, order_code)
        if order and order.status == OrderStatus.PENDING:
            order.status = OrderStatus.PAID
            await db.commit()
            await db.refresh(order)
            
            # Real-time notify
            await broadcast_order_update({
                "id": order.id,
                "order_code": order.order_code,
                "status": order.status,
                "amount": order.amount
            })
            
            return order
        return None

    @staticmethod
    async def cancel_order(db: AsyncSession, order_code: int):
        """Hủy đơn hàng chủ động bởi khách hàng hoặc do hết hạn."""
        order = await OrderService.get_order_by_code(db, order_code)
        if order and order.status == OrderStatus.PENDING:
            order.status = OrderStatus.CANCELLED
            await db.commit()
            await db.refresh(order)
            
            # Real-time notify
            await broadcast_order_update({
                "id": order.id,
                "order_code": order.order_code,
                "status": order.status,
                "amount": order.amount
            })
            
            return order
        return None
