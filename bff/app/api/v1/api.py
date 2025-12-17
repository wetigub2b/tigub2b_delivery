from fastapi import APIRouter

from app.api.v1.routes import admin, auth, driver, marks, order_actions, orders, prepare_goods, routes, stripe, warehouses

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(driver.router, prefix="/driver", tags=["driver"])
api_router.include_router(stripe.router, prefix="/driver/stripe", tags=["stripe"])
api_router.include_router(orders.router, prefix="/orders", tags=["orders"])
api_router.include_router(order_actions.router, prefix="/orders", tags=["order-actions"])
api_router.include_router(prepare_goods.router, prefix="/prepare-goods", tags=["prepare-goods"])
api_router.include_router(routes.router, prefix="/routes", tags=["routes"])
api_router.include_router(warehouses.router, prefix="/warehouses", tags=["warehouses"])
api_router.include_router(marks.router, prefix="/marks", tags=["marks"])
