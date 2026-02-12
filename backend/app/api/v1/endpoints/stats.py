from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.services.stats_service import StatsService
from fastapi.responses import Response

router = APIRouter()

@router.get("/")
async def get_stats(db: AsyncSession = Depends(get_db)):
    return await StatsService.get_system_stats(db)

@router.get("/revenue-chart")
async def get_revenue_chart(period: str = "week", db: AsyncSession = Depends(get_db)):
    return await StatsService.get_revenue_chart(db, period)

@router.get("/top-products")
async def get_top_products(limit: int = 5, db: AsyncSession = Depends(get_db)):
    return await StatsService.get_top_products(db, limit)

@router.get("/export")
async def export_excel(db: AsyncSession = Depends(get_db)):
    try:
        output = await StatsService.export_orders_excel(db)
        content = output.getvalue()
        
        headers = {
            'Content-Disposition': 'attachment; filename="orders_export.xlsx"'
        }
        return Response(content=content, headers=headers, media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    except Exception as e:
        import traceback
        error_msg = traceback.format_exc()
        print(error_msg)
        return Response(content=f"Error exporting: {error_msg}", status_code=500)
