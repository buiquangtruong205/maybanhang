from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.db.database import get_db
from app.services.iot_service import IOTService
from app.services.machine_service import MachineService

router = APIRouter()

class DispenseRequest(BaseModel):
    order_code: int
    success: bool

@router.get("/check-order/{order_code}")
async def check_order_iot(
    order_code: int, 
    x_machine_key: str = Header(None),
    db: AsyncSession = Depends(get_db)
):
    # Xác thực máy (Machine Key) từ Database
    # Hiện tại giả lập machine_id = 1, thực tế nên lấy từ key hoặc metadata
    is_valid = await MachineService.verify_secret_key(db, machine_id=1, secret_key=x_machine_key)
    if not is_valid:
         raise HTTPException(status_code=403, detail="Khóa máy không hợp lệ")

    result = await IOTService.process_dispense_request(db, order_code)
    
    if "error" in result:
        # Chuyển đổi thông báo lỗi sang tiếng Việt nếu cần
        error_msg = result["error"]
        if error_msg == "Order not found":
            error_msg = "Không tìm thấy đơn hàng"
        raise HTTPException(status_code=404, detail=error_msg)
        
    return result

@router.post("/dispense-complete")
async def dispense_complete(
    request: DispenseRequest,
    x_machine_key: str = Header(None),
    db: AsyncSession = Depends(get_db)
):
    # Xác thực máy
    is_valid = await MachineService.verify_secret_key(db, machine_id=1, secret_key=x_machine_key)
    if not is_valid:
         raise HTTPException(status_code=403, detail="Khóa máy không hợp lệ")
         
    success = await IOTService.handle_dispense_result(db, request.order_code, request.success)
    
    if not success:
        raise HTTPException(status_code=404, detail="Không tìm thấy đơn hàng")
        
    return {"success": True}
