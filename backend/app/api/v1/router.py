from fastapi import APIRouter

from app.api.v1.endpoints import (
    products,
    auth,
    users,
    machines,
    orders,
    payments,
    slots,
    issues,
    settings # New import
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(products.router, prefix="/products", tags=["Products"])
api_router.include_router(machines.router, prefix="/machines", tags=["Machines"])
api_router.include_router(orders.router, prefix="/orders", tags=["Orders"])
api_router.include_router(payments.router, prefix="", tags=["Payments"]) # Webhook
api_router.include_router(slots.router, prefix="/slots", tags=["Slots"])
api_router.include_router(issues.router, prefix="/issues", tags=["Issues"])
api_router.include_router(settings.router, prefix="/settings", tags=["System Settings"]) # Register
api_router.include_router(issues.router, prefix="/issues", tags=["issues"])
