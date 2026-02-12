from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.product import Product
from app.models.slot import Slot

class ProductService:
    @staticmethod
    async def get_all_products(db: AsyncSession, skip: int = 0, limit: int = 100, active_only: bool = True):
        """Lấy danh sách tất cả sản phẩm có phân trang."""
        query = select(Product)
        if active_only:
            query = query.where(Product.is_available == True)
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_product_by_id(db: AsyncSession, product_id: int):
        """Lấy chi tiết một sản phẩm theo ID."""
        result = await db.execute(select(Product).where(Product.id == product_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def check_stock(db: AsyncSession, product_id: int, machine_id: int) -> bool:
        """Kiểm tra xem sản phẩm còn hàng trong máy cụ thể không."""
        query = select(Slot).where(
            Slot.product_id == product_id,
            Slot.machine_id == machine_id,
            Slot.stock > 0
        )
        result = await db.execute(query)
        return result.scalar_one_or_none() is not None

    @staticmethod
    async def reduce_stock(db: AsyncSession, product_id: int, machine_id: int, quantity: int = 1):
        """Trừ kho sau khi bán hành thành công."""
        query = select(Slot).where(
            Slot.product_id == product_id,
            Slot.machine_id == machine_id
        )
        result = await db.execute(query)
        slot = result.scalar_one_or_none()
        if slot and slot.stock >= quantity:
            slot.stock -= quantity
            await db.commit()
            return True
        return False

    @staticmethod
    async def create_product(db: AsyncSession, product_data: dict):
        """Tạo sản phẩm mới."""
        new_product = Product(**product_data)
        db.add(new_product)
        await db.commit()
        await db.refresh(new_product)
        return new_product

    @staticmethod
    async def update_product(db: AsyncSession, product_id: int, update_data: dict):
        """Cập nhật thông tin sản phẩm."""
        product = await ProductService.get_product_by_id(db, product_id)
        if product:
            for key, value in update_data.items():
                setattr(product, key, value)
            await db.commit()
            await db.refresh(product)
            return product
        return None

    @staticmethod
    async def delete_product(db: AsyncSession, product_id: int):
        """Xóa sản phẩm."""
        product = await ProductService.get_product_by_id(db, product_id)
        if product:
            await db.delete(product)
            await db.commit()
            return True
        return False
