<script setup lang="ts">
/** 指标卡片：纯展示组件，不含任何业务逻辑 */
defineProps<{
  label: string
  value: string
  unit?: string
}>()
</script>

<template>
  <div class="metric-card">
    <div class="label">{{ label }}</div>
    <div class="value">
      {{ value }}
      <span v-if="unit" class="unit">{{ unit }}</span>
    </div>
  </div>
</template>

<style scoped>
.metric-card {
  background: #fff;
  border: 1px solid #e5e6eb;
  border-radius: 8px;
  padding: 16px 20px;
  min-width: 160px;
}

.label {
  font-size: 13px;
  color: #86909c;
  margin-bottom: 8px;
}

.value {
  font-size: 26px;
  font-weight: 600;
  color: #1d2129;
}

.unit {
  font-size: 13px;
  font-weight: 400;
  color: #86909c;
  margin-left: 4px;
}
</style>
