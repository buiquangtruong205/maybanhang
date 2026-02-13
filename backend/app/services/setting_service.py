from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.setting import SystemSetting
from typing import List, Optional

class SettingService:
    @staticmethod
    async def get_all_settings(db: AsyncSession) -> List[SystemSetting]:
        result = await db.execute(select(SystemSetting))
        return result.scalars().all()

    @staticmethod
    async def get_setting_by_key(db: AsyncSession, key: str) -> Optional[SystemSetting]:
        result = await db.execute(select(SystemSetting).where(SystemSetting.key == key))
        return result.scalars().first()

    @staticmethod
    async def update_setting(db: AsyncSession, key: str, value: str) -> Optional[SystemSetting]:
        setting = await SettingService.get_setting_by_key(db, key)
        if setting:
            setting.value = value
            await db.commit()
            await db.refresh(setting)
        return setting
    
    @staticmethod
    async def create_setting(db: AsyncSession, setting_data: dict) -> SystemSetting:
        setting = SystemSetting(**setting_data)
        db.add(setting)
        await db.commit()
        await db.refresh(setting)
        return setting

    @staticmethod
    async def initialize_defaults(db: AsyncSession):
        defaults = [
            # System Info
            {"key": "machine_id", "value": "VM001", "type": "string", "description": "Mã định danh máy", "group": "system"},
            {"key": "location_name", "value": "Sảnh Chính", "type": "string", "description": "Vị trí lắp đặt", "group": "system"},
            
            # Hardware
            {"key": "com_port", "value": "COM3", "type": "string", "description": "Cổng kết nối mạch đệm", "group": "hardware"},
            {"key": "baud_rate", "value": "9600", "type": "number", "description": "Tốc độ truyền Serial", "group": "hardware"},
            
            # Payment
            {"key": "payment_timeout", "value": "90", "type": "number", "description": "Thời gian chờ thanh toán (giây)", "group": "payment"},
            {"key": "bank_name", "value": "MBBank", "type": "string", "description": "Ngân hàng thụ hưởng", "group": "payment"},
             
            # Operation
             {"key": "maintenance_mode", "value": "false", "type": "boolean", "description": "Chế độ bảo trì", "group": "system"},
        ]
        
        for d in defaults:
            exists = await SettingService.get_setting_by_key(db, d["key"])
            if not exists:
                await SettingService.create_setting(db, d)
