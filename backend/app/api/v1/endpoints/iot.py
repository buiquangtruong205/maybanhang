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


async def _get_machine_from_key(
    x_machine_key: str = Header(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Dependency chung: Xác thực X-Machine-Key header và trả về machine object.
    Tự động tra cứu machine_id từ secret_key thay vì hardcode.
    """
    if not x_machine_key:
        raise HTTPException(status_code=401, detail="Thiếu header X-Machine-Key")

    machine = await MachineService.get_by_secret_key(db, secret_key=x_machine_key)
    if not machine:
        raise HTTPException(status_code=403, detail="Khóa máy không hợp lệ")

    return machine


@router.get("/check-order/{order_code}")
async def check_order_iot(
    order_code: int,
    machine=Depends(_get_machine_from_key),
    db: AsyncSession = Depends(get_db)
):
    """
    ESP32 gọi API này để kiểm tra đơn hàng đã thanh toán chưa.
    Nếu đã PAID → trả về should_dispense=True để máy nhả hàng.
    """
    result = await IOTService.process_dispense_request(db, order_code)

    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    # Gắn thêm machine_id để ESP32 biết máy nào đang xử lý
    result["machine_id"] = machine.id
    return result


@router.post("/dispense-complete")
async def dispense_complete(
    request: DispenseRequest,
    machine=Depends(_get_machine_from_key),
    db: AsyncSession = Depends(get_db)
):
    """
    ESP32 gọi API này sau khi nhả hàng xong (thành công hoặc thất bại).
    Cập nhật trạng thái đơn hàng → COMPLETED hoặc FAILED.
    """
    success = await IOTService.handle_dispense_result(db, request.order_code, request.success)

    if not success:
        raise HTTPException(status_code=404, detail="Không tìm thấy đơn hàng")

    return {"success": True, "machine_id": machine.id}


@router.post("/heartbeat")
async def machine_heartbeat(
    machine=Depends(_get_machine_from_key),
    db: AsyncSession = Depends(get_db)
):
    """
    ESP32 gọi API này định kỳ (vd: 30s/lần) để báo cáo máy vẫn online.
    Cập nhật trường 'last_heartbeat' và 'status' trong cơ sở dữ liệu.
    """
    success = await MachineService.update_heartbeat(db, machine.id)
    if not success:
        raise HTTPException(status_code=404, detail="Không thể cập nhật nhịp tim")
    
    return {"status": "online", "machine_id": machine.id}
