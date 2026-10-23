<script setup lang="ts">
/**
 * 阶段 1 竖线页面：调参数 → 点按钮 → 看 4 个指标。
 * 页面里没有任何异步逻辑，都封装在 useSimulationTask 里。
 */
import { ref } from 'vue'
import MetricCard from './components/MetricCard.vue'
import { useSimulationTask } from './composables/useSimulationTask'

const { store, isRunning, statusText, metrics, run } = useSimulationTask()

const trucks = ref(4)
const shiftMinutes = ref(120)

async function onStart() {
  await run({ trucks: trucks.value, shift_minutes: shiftMinutes.value, seed: 42 })
}
</script>

<template>
  <div class="app">
    <h1>矿山运力仿真 · 最小测算</h1>
    <p class="sub">1 个装载点 + 1 个卸载点 + N 台卡车，跑一个班次</p>

    <div class="panel">
      <label>
        卡车数
        <input v-model.number="trucks" type="number" min="1" max="20" :disabled="isRunning" />
      </label>
      <label>
        班次（分钟）
        <input
          v-model.number="shiftMinutes"
          type="number"
          min="1"
          max="1440"
          :disabled="isRunning"
        />
      </label>
      <button :disabled="isRunning" @click="onStart">
        {{ isRunning ? '仿真中…' : '开始仿真' }}
      </button>
      <span class="status">状态：{{ statusText }}</span>
      <span v-if="store.taskId" class="task-id">task={{ store.taskId }}</span>
    </div>

    <p v-if="store.error" class="error">出错了：{{ store.error }}</p>

    <div v-if="metrics.length" class="metrics">
      <MetricCard
        v-for="m in metrics"
        :key="m.label"
        :label="m.label"
        :value="m.value"
        :unit="m.unit"
      />
    </div>
  </div>
</template>

<style scoped>
.app {
  padding: 32px;
  max-width: 960px;
  margin: 0 auto;
}

.sub {
  margin-bottom: 20px;
}

.panel {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
  background: #fff;
  border: 1px solid #e5e6eb;
  border-radius: 8px;
  padding: 16px 20px;
}

.panel label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #4e5969;
}

.panel input {
  width: 90px;
  padding: 6px 8px;
  border: 1px solid #e5e6eb;
  border-radius: 4px;
}

button {
  padding: 8px 20px;
  background: #165dff;
  color: #fff;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

button:disabled {
  background: #94bfff;
  cursor: not-allowed;
}

.status,
.task-id {
  font-size: 13px;
  color: #86909c;
}

.error {
  margin-top: 16px;
  color: #d03050;
}

.metrics {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
  margin-top: 20px;
}
</style>
