from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.slot import Slot

class SlotService:
    @staticmethod
    async def get_slot_by_id(db: AsyncSession, slot_id: int):
        result = await db.execute(select(Slot).where(Slot.id == slot_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def list_slots(db: AsyncSession, machine_id: int = None):
        query = select(Slot)
        if machine_id:
            query = query.where(Slot.machine_id == machine_id)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def create_slot(db: AsyncSession, slot_data: dict):
        new_slot = Slot(**slot_data)
        db.add(new_slot)
        await db.commit()
        await db.refresh(new_slot)
        return new_slot

    @staticmethod
    async def update_slot(db: AsyncSession, slot_id: int, update_data: dict):
        slot = await SlotService.get_slot_by_id(db, slot_id)
        if slot:
            for key, value in update_data.items():
                setattr(slot, key, value)
            await db.commit()
            await db.refresh(slot)
            return slot
        return None

    @staticmethod
    async def delete_slot(db: AsyncSession, slot_id: int):
        slot = await SlotService.get_slot_by_id(db, slot_id)
        if slot:
            await db.delete(slot)
            await db.commit()
            return True
        return False

    @staticmethod
    async def refill_slot(db: AsyncSession, slot_id: int):
        slot = await SlotService.get_slot_by_id(db, slot_id)
        if slot:
            slot.stock = slot.capacity
            await db.commit()
            await db.refresh(slot)
            return slot
        return None
