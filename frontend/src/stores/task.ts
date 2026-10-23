/**
 * 仿真任务的共享状态。
 *
 * 为什么用 Pinia 而不是组件内的 ref：
 * 提交在页面 A、结果展示在组件 B，状态需要跨组件共享；
 * 后面加"任务列表"页面时，直接复用同一个 store。
 */

import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getTask, submitSimulation } from '../api/simulations'
import type { Kpi, SimulationConfig, TaskStatus } from '../types/simulation'

export const useTaskStore = defineStore('task', () => {
  const taskId = ref<string | null>(null)
  const status = ref<TaskStatus | null>(null)
  const progress = ref(0)
  const kpi = ref<Kpi | null>(null)
  const error = ref<string | null>(null)
  const submitting = ref(false)

  /** 提交仿真：拿到 taskId 就返回，不等待结果 */
  async function submit(config: Partial<SimulationConfig>) {
    submitting.value = true
    error.value = null
    kpi.value = null
    progress.value = 0
    try {
      const created = await submitSimulation(config)
      taskId.value = created.task_id
      status.value = created.status
    } catch (e) {
      error.value = e instanceof Error ? e.message : String(e)
      throw e
    } finally {
      submitting.value = false
    }
  }

  /**
   * 轮询直到任务结束。
   * 阶段 1 用轮询（30 行搞定）；阶段 5 换成 WebSocket 推送进度。
   * 必须有次数上限，否则后端挂了前端会一直转圈。
   */
  async function pollUntilDone(maxTimes = 30, intervalMs = 1000): Promise<void> {
    if (!taskId.value) return

    for (let i = 0; i < maxTimes; i++) {
      const view = await getTask(taskId.value)
      status.value = view.status
      progress.value = view.progress

      if (view.status === 'SUCCEEDED') {
        kpi.value = view.kpi
        return
      }
      if (view.status === 'FAILED') {
        error.value = view.error_message ?? '仿真失败'
        return
      }
      await new Promise((resolve) => setTimeout(resolve, intervalMs))
    }
    error.value = '轮询超时：任务仍未结束'
  }

  function reset() {
    taskId.value = null
    status.value = null
    progress.value = 0
    kpi.value = null
    error.value = null
  }

  return { taskId, status, progress, kpi, error, submitting, submit, pollUntilDone, reset }
})
