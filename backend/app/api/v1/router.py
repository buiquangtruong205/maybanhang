from fastapi import APIRouter

from app.api.v1.endpoints import products, payments, orders, iot, auth, machines, stats, slots, users, issues

api_router = APIRouter()

api_router.include_router(products.router, prefix="/products", tags=["products"])
api_router.include_router(payments.router, prefix="/payments", tags=["payments"])
api_router.include_router(orders.router, prefix="/orders", tags=["orders"])
api_router.include_router(iot.router, prefix="/iot", tags=["iot"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(machines.router, prefix="/machines", tags=["machines"])
api_router.include_router(stats.router, prefix="/stats", tags=["stats"])
api_router.include_router(slots.router, prefix="/slots", tags=["slots"])
api_router.include_router(issues.router, prefix="/issues", tags=["issues"])
