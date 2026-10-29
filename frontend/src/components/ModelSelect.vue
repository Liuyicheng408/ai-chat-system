<script setup>
defineProps({
  modelValue: { type: String, default: '' },
  models: { type: Array, default: () => [] },
})
const emit = defineEmits(['change'])

function statusText(m) {
  if (m.type === 'remote') return m.status === 'ready' ? '在线' : '未配置'
  return m.status === 'loaded' ? '已加载' : '未加载'
}
</script>

<template>
  <el-select
    :model-value="modelValue"
    class="model-select"
    popper-class="model-popper"
    @update:model-value="(v) => emit('change', v)"
  >
    <template #prefix>
      <span class="pulse" :class="models.find((m) => m.id === modelValue)?.status"></span>
    </template>
    <el-option v-for="m in models" :key="m.id" :value="m.id" :label="m.name">
      <div class="opt">
        <span class="dot" :class="[m.type, m.status]"></span>
        <div class="opt-text">
          <div class="opt-name">{{ m.name }}</div>
          <div class="opt-sub">{{ m.kind_label }} · {{ statusText(m) }}</div>
        </div>
        <span class="tag" :class="m.type">{{ m.type === 'remote' ? 'API' : '本地' }}</span>
      </div>
    </el-option>
  </el-select>
</template>

<style scoped>
.model-select {
  width: 210px;
}
.pulse {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--text-3);
  display: inline-block;
  margin-right: 2px;
}
.pulse.ready,
.pulse.loaded {
  background: var(--success);
  box-shadow: 0 0 0 3px rgba(34, 197, 94, 0.15);
}
.opt {
  display: flex;
  align-items: center;
  gap: 9px;
  padding: 3px 0;
}
.opt-text {
  flex: 1;
  min-width: 0;
}
.opt-name {
  font-size: 13px;
  font-weight: 550;
  color: var(--text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.opt-sub {
  font-size: 11px;
  color: var(--text-3);
}
.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--text-3);
  flex: none;
}
.dot.loaded,
.dot.ready {
  background: var(--success);
}
.dot.unconfigured {
  background: var(--danger);
}
.tag {
  font-size: 10px;
  padding: 1px 6px;
  border-radius: 5px;
  background: var(--bg-soft);
  color: var(--text-2);
  border: 1px solid var(--border);
}
.tag.remote {
  color: #0ea5e9;
  border-color: rgba(14, 165, 233, 0.3);
  background: rgba(14, 165, 233, 0.08);
}
.tag.local {
  color: #8b5cf6;
  border-color: rgba(139, 92, 246, 0.3);
  background: rgba(139, 92, 246, 0.08);
}
</style>
