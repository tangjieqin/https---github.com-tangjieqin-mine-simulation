/**
 * 把"提交 + 轮询 + 取结果"封装成一个动作，页面只需要调用 run()。
 *
 * store 负责存状态，这个 composable 负责编排流程 —— 分层之后，
 * 页面组件里就只剩模板和事件绑定，不会有异步逻辑。
 */

import { computed } from 'vue'
import { useTaskStore } from '../stores/task'
import type { SimulationConfig } from '../types/simulation'
import { formatMinutes, formatPercent, formatTonnage } from '../utils/format'

export function useSimulationTask() {
  const store = useTaskStore()

  const isRunning = computed(
    () => store.submitting || store.status === 'PENDING' || store.status === 'RUNNING',
  )

  const statusText = computed(() => {
    switch (store.status) {
      case 'PENDING':
        return '排队中…'
      case 'RUNNING':
        return '仿真中…'
      case 'SUCCEEDED':
        return '完成'
      case 'FAILED':
        return '失败'
      default:
        return '未开始'
    }
  })

  /** 把 KPI 转成卡片可以直接渲染的形态 */
  const metrics = computed(() => {
    const k = store.kpi
    if (!k) return []
    return [
      { label: '总产量', value: formatTonnage(k.tonnage_t), unit: 't' },
      { label: '循环次数', value: String(k.cycles), unit: '次' },
      { label: '卡车利用率', value: formatPercent(k.truck_utilization), unit: '' },
      { label: '平均等装', value: formatMinutes(k.avg_wait_load_min), unit: 'min' },
    ]
  })

  async function run(config: Partial<SimulationConfig>) {
    try {
      await store.submit(config)
      await store.pollUntilDone()
    } catch {
      // store.error 已经有值，这里吞掉异常，避免控制台红色报错
    }
  }

  return { store, isRunning, statusText, metrics, run }
}
