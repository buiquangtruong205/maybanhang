from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from app.models.log import RefillLog
from typing import List, Optional

class LogService:
    @staticmethod
    async def create_refill_log(
        db: AsyncSession, 
        user_id: int, 
        machine_id: int, 
        slot_id: int, 
        product_id: int, 
        quantity: int,
        old_quantity: int,
        new_quantity: int
    ) -> RefillLog:
        log = RefillLog(
            user_id=user_id,
            machine_id=machine_id,
            slot_id=slot_id,
            product_id=product_id,
            quantity=quantity,
            old_quantity=old_quantity,
            new_quantity=new_quantity
        )
        db.add(log)
        await db.commit()
        await db.refresh(log)
        return log

    @staticmethod
    async def get_refill_logs(
        db: AsyncSession, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[RefillLog]:
        result = await db.execute(
            select(RefillLog)
            .order_by(RefillLog.timestamp.desc())
            .options(
                joinedload(RefillLog.user),
                joinedload(RefillLog.machine),
                joinedload(RefillLog.product),
                joinedload(RefillLog.slot)
            )
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
