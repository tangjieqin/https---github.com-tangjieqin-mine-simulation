/**
 * 仿真接口。页面只调这里，不直接碰 fetch。
 */

import { request } from './client'
import type { SimulationConfig, TaskCreated, TaskView } from '../types/simulation'

/** 提交仿真：立即返回 task_id（后端 202，不会等仿真跑完） */
export function submitSimulation(config: Partial<SimulationConfig>): Promise<TaskCreated> {
  return request<TaskCreated>('/simulations', {
    method: 'POST',
    body: JSON.stringify(config),
  })
}

/** 查询任务状态与结果 */
export function getTask(taskId: string): Promise<TaskView> {
  return request<TaskView>(`/simulations/${taskId}`)
}
