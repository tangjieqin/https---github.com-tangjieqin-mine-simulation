"""mine-simulation 后端入口（阶段 0 骨架）。

启动：
    cd backend && .venv/Scripts/python.exe -m uvicorn main:app --reload --port 8000
验证：
    http://127.0.0.1:8000/api/v1/health  ->  {"status":"ok"}
    http://127.0.0.1:8000/docs           ->  交互式接口文档
"""

from fastapi import FastAPI

app = FastAPI(title="mine-simulation", version="0.0.1")


@app.get("/api/v1/health")
def health() -> dict:
    return {"status": "ok"}
