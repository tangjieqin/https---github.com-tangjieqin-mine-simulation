/** 数值格式化：后端给的是原始数字，展示形态在这里统一处理 */

/** 吨位：千分位 + 保留 1 位小数 */
export function formatTonnage(t: number): string {
  return t.toLocaleString('zh-CN', { minimumFractionDigits: 1, maximumFractionDigits: 1 })
}

/** 利用率：后端是 0~1 小数，这里转成百分比字符串 */
export function formatPercent(ratio: number): string {
  return `${(ratio * 100).toFixed(2)}%`
}

/** 分钟：保留 2 位小数 */
export function formatMinutes(min: number): string {
  return min.toFixed(2)
}
