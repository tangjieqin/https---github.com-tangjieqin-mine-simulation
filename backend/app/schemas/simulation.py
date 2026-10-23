"""仿真相关的数据模型（请求/响应结构）。

对应前端 `src/types/simulation.ts`，两边字段必须一致。
`extra="forbid"` 表示：传了没定义的字段直接 422，防止前端字段名拼错却静默生效。
"""

from pydantic import BaseModel, ConfigDict, Field


class SimulationConfig(BaseModel):
    """一次仿真的输入参数。"""

    model_config = ConfigDict(extra="forbid")

    trucks: int = Field(default=2, ge=1, le=20, description="卡车数量")
    shift_minutes: float = Field(default=60.0, gt=0, le=1440, description="班次时长（仿真分钟）")
    truck_capacity_t: float = Field(default=100.0, gt=0, le=400, description="单车载重（吨）")
    load_min: float = Field(default=4.0, gt=0, description="装载耗时（分钟）")
    dump_min: float = Field(default=2.0, gt=0, description="卸载耗时（分钟）")
    travel_loaded_min: float = Field(default=12.0, gt=0, description="重车行驶耗时（分钟）")
    travel_empty_min: float = Field(default=9.0, gt=0, description="空车返回耗时（分钟）")
    seed: int = Field(default=42, ge=0, description="随机种子，同 seed 结果必须一致")


class Kpi(BaseModel):
    """仿真输出的 4 个指标。utilization 统一用 0~1 小数，前端显示时再乘 100。"""

    tonnage_t: float = Field(description="总产量（吨）")
    cycles: int = Field(description="完成的循环次数")
    truck_utilization: float = Field(ge=0, le=1, description="卡车利用率（0~1）")
    avg_wait_load_min: float = Field(ge=0, description="平均等装时间（分钟）")


class TaskCreated(BaseModel):
    """提交仿真后的立即返回（202）。"""

    task_id: str
    status: str


class TaskView(BaseModel):
    """任务查询结果。前端靠 status 判断该继续轮询还是渲染结果。"""

    task_id: str
    status: str  # PENDING / RUNNING / SUCCEEDED / FAILED
    progress: float = 0.0
    kpi: Kpi | None = None
    error_message: str | None = None
    created_at: str | None = None
    finished_at: str | None = None
