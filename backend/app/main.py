"""mine-simulation 后端入口。

启动（在 backend/ 目录）：
    .venv/Scripts/python.exe -m uvicorn app.main:app --reload --port 8000

验证：
    http://127.0.0.1:8000/api/v1/health   ->  {"status":"ok"}
    http://127.0.0.1:8000/docs            ->  交互式接口文档

这里只做一件事：创建 app 并注册路由。业务逻辑一律在 api/v1 → services → simulation 里。
"""

from fastapi import FastAPI

from app.api.v1 import api_router

app = FastAPI(title="mine-simulation", version="0.1.0")

app.include_router(api_router)
