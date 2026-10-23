/**
 * 与后端 Pydantic 模型一一对应的类型。
 * 文件位置：backend/app/schemas/simulation.py
 *
 * 后续可以用下面这条命令从 OpenAPI 自动生成，避免手写漂移：
 *   npx openapi-typescript http://127.0.0.1:8000/openapi.json -o src/types/schema.d.ts
 */

export type TaskStatus = 'PENDING' | 'RUNNING' | 'SUCCEEDED' | 'FAILED'

/** 提交仿真的入参（全部可选，后端有默认值） */
export interface SimulationConfig {
  trucks: number
  shift_minutes: number
  truck_capacity_t: number
  load_min: number
  dump_min: number
  travel_loaded_min: number
  travel_empty_min: number
  seed: number
}

/** 仿真输出的 4 个指标。utilization 是 0~1 小数，显示时再乘 100 */
export interface Kpi {
  tonnage_t: number
  cycles: number
  truck_utilization: number
  avg_wait_load_min: number
}

/** POST /simulations 的返回（202） */
export interface TaskCreated {
  task_id: string
  status: TaskStatus
}

/** GET /simulations/{id} 的返回 */
export interface TaskView {
  task_id: string
  status: TaskStatus
  progress: number
  kpi: Kpi | null
  error_message: string | null
  created_at: string | null
  finished_at: string | null
}
