from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.machine import Machine

class MachineService:
    @staticmethod
    async def get_machine_by_id(db: AsyncSession, machine_id: int):
        """Lấy thông tin máy bán hàng."""
        result = await db.execute(select(Machine).where(Machine.id == machine_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def verify_secret_key(db: AsyncSession, machine_id: int, secret_key: str) -> bool:
        """Xác thực Machine Key (X-Machine-Key)."""
        machine = await MachineService.get_machine_by_id(db, machine_id)
        if machine and machine.secret_key == secret_key:
            return True
        return False

    @staticmethod
    async def update_heartbeat(db: AsyncSession, machine_id: int):
        """Cập nhật thời gian phản hồi cuối cùng của máy."""
        machine = await MachineService.get_machine_by_id(db, machine_id)
        if machine:
            machine.status = "online"
            await db.commit()
            return True
        return False

    @staticmethod
    async def list_machines(db: AsyncSession, skip: int = 0, limit: int = 100):
        """Liệt kê danh sách máy bán hàng."""
        result = await db.execute(select(Machine).offset(skip).limit(limit))
        return result.scalars().all()

    @staticmethod
    async def create_machine(db: AsyncSession, machine_data: dict):
        """Tạo máy bán hàng mới."""
        new_machine = Machine(**machine_data)
        db.add(new_machine)
        await db.commit()
        await db.refresh(new_machine)
        return new_machine

    @staticmethod
    async def update_machine(db: AsyncSession, machine_id: int, update_data: dict):
        """Cập nhật thông tin máy."""
        machine = await MachineService.get_machine_by_id(db, machine_id)
        if machine:
            for key, value in update_data.items():
                setattr(machine, key, value)
            await db.commit()
            await db.refresh(machine)
            return machine
        return None

    @staticmethod
    async def delete_machine(db: AsyncSession, machine_id: int):
        """Xóa máy bán hàng."""
        machine = await MachineService.get_machine_by_id(db, machine_id)
        if machine:
            await db.delete(machine)
            await db.commit()
            return True
        return False
