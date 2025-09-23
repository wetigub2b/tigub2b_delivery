from fastapi import APIRouter

from app.api.v1.routes import auth, orders, routes, warehouses

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(orders.router, prefix="/orders", tags=["orders"])
api_router.include_router(routes.router, prefix="/routes", tags=["routes"])
api_router.include_router(warehouses.router, prefix="/warehouses", tags=["warehouses"])
