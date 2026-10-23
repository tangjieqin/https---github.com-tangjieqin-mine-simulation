"""仿真任务接口（阶段 1 竖线的两端）。

POST /api/v1/simulations      提交仿真，立即返回 202 + task_id
GET  /api/v1/simulations/{id}  查询任务状态与结果

路由层只做三件事：接收参数、调 service、组织响应。
不放任何仿真逻辑，也不放任务存储逻辑。
"""

from fastapi import APIRouter, HTTPException

from app.schemas.simulation import SimulationConfig, TaskCreated, TaskView
from app.services import simulation_service

router = APIRouter(prefix="/simulations", tags=["simulations"])


@router.post("", status_code=202, response_model=TaskCreated)
def submit_simulation(config: SimulationConfig) -> TaskCreated:
    """提交仿真。

    注意是 202 不是 200：请求已被接受但尚未完成，
    绝不能在这里等待仿真跑完（会堵死网关）。
    """
    task_id = simulation_service.submit(config.model_dump())
    return TaskCreated(task_id=task_id, status="PENDING")


@router.get("/{task_id}", response_model=TaskView)
def get_simulation(task_id: str) -> TaskView:
    """查询任务。status=SUCCEEDED 时 kpi 才有值。"""
    task = simulation_service.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"任务不存在: {task_id}")

    return TaskView(
        task_id=task["task_id"],
        status=task["status"],
        progress=task["progress"],
        kpi=task["kpi"],
        error_message=task["error_message"],
        created_at=task["created_at"],
        finished_at=task["finished_at"],
    )
