"""v1 路由聚合。

所有 v1 接口统一挂到 /api/v1 前缀下，将来加 v2 只需新增一个包。
"""

from fastapi import APIRouter

from app.api.v1 import health, simulations

api_router = APIRouter()
api_router.include_router(health.router, prefix="/api/v1")
api_router.include_router(simulations.router, prefix="/api/v1")
