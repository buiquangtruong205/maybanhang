from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, case
from app.models.order import Order
from app.models.product import Product
from app.models.machine import Machine
from datetime import datetime, timedelta
import xlsxwriter
import io

class StatsService:
    @staticmethod
    async def get_system_stats(db: AsyncSession):
        # 1. Total Revenue (Paid, Dispensing or Completed orders)
        query_rev = select(func.sum(Order.amount)).where(Order.status.in_(["PAID", "DISPENSING", "COMPLETED"]))
        total_revenue = (await db.execute(query_rev)).scalar() or 0

        # 2. Orders Count
        query_total_orders = select(func.count(Order.id))
        total_orders = (await db.execute(query_total_orders)).scalar() or 0
        
        query_completed = select(func.count(Order.id)).where(Order.status == "COMPLETED")
        completed_orders = (await db.execute(query_completed)).scalar() or 0

        query_paid = select(func.count(Order.id)).where(Order.status.in_(["PAID", "DISPENSING", "COMPLETED"]))
        paid_orders = (await db.execute(query_paid)).scalar() or 0

        # 3. Machines
        query_total_machines = select(func.count(Machine.id))
        total_machines = (await db.execute(query_total_machines)).scalar() or 0

        query_online = select(func.count(Machine.id)).where(Machine.status == "online")
        online_machines = (await db.execute(query_online)).scalar() or 0

        return {
            "total_revenue": total_revenue,
            "total_orders": total_orders,
            "completed_orders": completed_orders,
            "paid_orders": paid_orders,
            "total_machines": total_machines,
            "online_machines": online_machines
        }

    @staticmethod
    async def get_revenue_chart(db: AsyncSession, period: str = 'week'):
        now = datetime.now()
        data = []
        labels = []
        
        if period == 'week':
            # Last 7 days
            start_date = now - timedelta(days=6)
            current = start_date
            while current <= now:
                labels.append(current.strftime("%d/%m"))
                # Query for this day
                day_start = current.replace(hour=0, minute=0, second=0, microsecond=0)
                day_end = current.replace(hour=23, minute=59, second=59, microsecond=999999)
                
                query = select(func.sum(Order.amount)).where(
                    Order.created_at >= day_start,
                    Order.created_at <= day_end,
                    Order.status.in_(["PAID", "DISPENSING", "COMPLETED"])
                )
                result = await db.execute(query)
                total = result.scalar() or 0
                data.append(total)
                current += timedelta(days=1)
                
        elif period == 'month':
            # Last 30 days
            start_date = now - timedelta(days=29)
            current = start_date
            while current <= now:
                labels.append(current.strftime("%d/%m"))
                day_start = current.replace(hour=0, minute=0, second=0, microsecond=0)
                day_end = current.replace(hour=23, minute=59, second=59, microsecond=999999)
                
                query = select(func.sum(Order.amount)).where(
                    Order.created_at >= day_start,
                    Order.created_at <= day_end,
                    Order.status.in_(["PAID", "DISPENSING", "COMPLETED"])
                )
                result = await db.execute(query)
                total = result.scalar() or 0
                data.append(total)
                current += timedelta(days=1)

        return {"labels": labels, "data": data}

    @staticmethod
    async def get_top_products(db: AsyncSession, limit: int = 5):
        # Query Order directly since it has product_id
        # Group by Product.id, sum 1 (quantity) per order? 
        # Wait, Order doesn't have quantity. It assumes 1 item per order?
        # Yes, based on schema.
        
        query = (
            select(
                Product.name,
                func.count(Order.id).label("total_sold"),
                func.sum(Order.amount).label("total_revenue")
            )
            .join(Order.product)
            .where(Order.status.in_(["PAID", "DISPENSING", "COMPLETED"]))
            .group_by(Product.id, Product.name)
            .order_by(desc("total_sold"))
            .limit(limit)
        )
        
        result = await db.execute(query)
        rows = result.all()
        return [
            {"name": r.name, "sold": r.total_sold, "revenue": r.total_revenue}
            for r in rows
        ]

    @staticmethod
    async def export_orders_excel(db: AsyncSession):
        # Join Product to get product name (Outer join in case product is deleted)
        query = (
            select(Order, Product.name.label("product_name"))
            .outerjoin(Order.product)
            .order_by(desc(Order.created_at))
            .limit(1000)
        )
        result = await db.execute(query)
        rows = result.all() # list of (Order, product_name)
        
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet("Orders")
        
        # Headers
        headers = ["Mã đơn", "Ngày tạo", "Sản phẩm", "Tổng tiền", "Trạng thái", "QR Code"]
        header_format = workbook.add_format({'bold': True, 'bg_color': '#D3D3D3', 'border': 1})
        for col, h in enumerate(headers):
            worksheet.write(0, col, h, header_format)
            
        # Data
        date_format = workbook.add_format({'num_format': 'dd/mm/yyyy hh:mm'})
        money_format = workbook.add_format({'num_format': '#,##0'})
        
        row = 1
        for r in rows:
            order = r[0]
            product_name = r[1] or "Unknown"
            
            # Remove timezone for xlsxwriter compatibility
            c_at = order.created_at.replace(tzinfo=None) if order.created_at else None

            worksheet.write(row, 0, order.order_code)
            worksheet.write(row, 1, c_at, date_format)
            worksheet.write(row, 2, product_name)
            worksheet.write(row, 3, order.amount or 0, money_format)
            worksheet.write(row, 4, str(order.status))
            worksheet.write(row, 5, order.qr_code or "")
            row += 1
            
        worksheet.set_column(0, 0, 15)
        worksheet.set_column(1, 1, 20)
        worksheet.set_column(2, 2, 25)
        worksheet.set_column(3, 3, 15)
        
        workbook.close()
        output.seek(0)
        return output
