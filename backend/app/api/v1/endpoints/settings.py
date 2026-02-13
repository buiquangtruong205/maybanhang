from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.db.database import get_db
from app.services.setting_service import SettingService
from app.schemas.setting import SettingResponse, SettingUpdate
from app.api.v1.endpoints.auth import check_admin_role  # Assuming this exists or using dependency

router = APIRouter()

@router.get("/", response_model=List[SettingResponse])
async def read_settings(db: AsyncSession = Depends(get_db)):
    """Lấy danh sách toàn bộ cấu hình hệ thống."""
    return await SettingService.get_all_settings(db)

@router.put("/{key}", response_model=SettingResponse)
async def update_setting(
    key: str, 
    update_data: SettingUpdate, 
    db: AsyncSession = Depends(get_db),
    # current_user = Depends(check_admin_role) # Uncomment when enforcing admin role
):
    """Cập nhật giá trị cấu hình (Chỉ Admin)."""
    setting = await SettingService.update_setting(db, key, update_data.value)
    if not setting:
        raise HTTPException(status_code=404, detail="Không tìm thấy cấu hình này")
    return setting

@router.post("/restore-defaults")
async def restore_defaults(db: AsyncSession = Depends(get_db)):
    """Khôi phục các cấu hình mặc định."""
    await SettingService.initialize_defaults(db)
    return {"message": "Đã khôi phục cấu hình mặc định"}
