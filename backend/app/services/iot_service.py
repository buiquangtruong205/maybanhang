from sqlalchemy.ext.asyncio import AsyncSession
from app.services.order_service import OrderService
from app.services.product_service import ProductService
from app.models.order import OrderStatus

class IOTService:
    """
    Dịch vụ giao tiếp với thiết bị (phi phần cứng).
    Sử dụng để xử lý logic khi nhận tín hiệu từ MQTT hoặc API từ máy.
    """
    
    @staticmethod
    async def process_dispense_request(db: AsyncSession, order_code: int):
        """
        Kiểm tra và chuẩn bị dữ liệu để yêu cầu máy nhả hàng.
        """
        order = await OrderService.get_order_by_code(db, order_code)
        if not order:
            return {"error": "Order not found", "should_dispense": False}
            
        # Chỉ cho phép nhả hàng nếu đơn đã thanh toán (PAID)
        # Hoặc đang trong quá trình (DISPENSING)
        should_dispense = order.status == OrderStatus.PAID
        
        return {
            "order_code": order.order_code,
            "status": order.status,
            "should_dispense": should_dispense
        }

    @staticmethod
    async def handle_dispense_result(db: AsyncSession, order_code: int, success: bool):
        """
        Xử lý kết quả trả về từ máy sau khi thực hiện nhả hàng.
        """
        order = await OrderService.get_order_by_code(db, order_code)
        if not order:
            return False
            
        if success:
            # 1. Cập nhật đơn hàng thành công
            await OrderService.update_status(db, order.id, OrderStatus.COMPLETED)
            # 2. Trừ kho sản phẩm
            await ProductService.reduce_stock(db, order.product_id, order.machine_id)
        else:
            # Cập nhật đơn hàng thất bại
            await OrderService.update_status(db, order.id, OrderStatus.FAILED)
            
        return True
