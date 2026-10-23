"""健康检查：用来确认服务活着，前端/部署脚本都会打这个接口。"""

from fastapi import APIRouter

router = APIRouter(tags=["health"])

@router.get("/health")
def health() -> dict:
    return {"status": "ok"}
