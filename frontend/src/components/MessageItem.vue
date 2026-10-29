<script setup>
import { computed, ref } from 'vue'
import { ElMessage } from 'element-plus'
import MarkdownBlock from './MarkdownBlock.vue'

const props = defineProps({
  message: { type: Object, required: true },
  userName: { type: String, default: '我' },
  userInitial: { type: String, default: 'U' },
  modelName: { type: String, default: '' },
})

const isUser = computed(() => props.message.role === 'user')
const timeText = computed(() => {
  const raw = props.message.created_at
  if (!raw) return ''
  const d = new Date(raw)
  if (Number.isNaN(d.getTime())) return ''
  return d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
})

const copied = ref(false)
async function copy() {
  try {
    await navigator.clipboard.writeText(props.message.content || '')
    copied.value = true
    ElMessage.success('已复制')
    setTimeout(() => (copied.value = false), 1500)
  } catch (e) {
    ElMessage.error('复制失败')
  }
}
</script>

<template>
  <div :class="['msg-row', isUser ? 'is-user' : 'is-ai']">
    <div class="avatar" :class="isUser ? 'avatar-user' : 'avatar-ai'">
      <template v-if="isUser">{{ userInitial }}</template>
      <template v-else><span class="ai-glyph">AI</span></template>
    </div>

    <div class="msg-main">
      <div class="msg-meta">
        <span class="name">{{ isUser ? userName : 'AI 助手' }}</span>
        <span v-if="message.model_id" class="model-tag">{{ modelName || message.model_id }}</span>
        <span class="time">{{ timeText }}</span>
      </div>

      <div class="bubble" :class="isUser ? 'bubble-user' : 'bubble-ai'">
        <div v-if="isUser" class="plain">{{ message.content }}</div>
        <template v-else>
          <MarkdownBlock v-if="message.content" :content="message.content" />
          <div v-if="message.streaming && !message.content" class="thinking">
            <span></span><span></span><span></span>
          </div>
          <span v-if="message.streaming && message.content" class="caret"></span>
          <div v-if="message.error" class="err">{{ message.error }}</div>
        </template>
      </div>

      <div v-if="!isUser && message.content && !message.streaming" class="msg-actions">
        <button class="act" @click="copy">
          <el-icon><CopyDocument /></el-icon>{{ copied ? '已复制' : '复制' }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.msg-row {
  display: flex;
  gap: 12px;
  padding: 6px 0 18px;
  animation: rise 0.25s ease;
}
.msg-row.is-user {
  flex-direction: row-reverse;
}
@keyframes rise {
  from {
    opacity: 0;
    transform: translateY(6px);
  }
  to {
    opacity: 1;
    transform: none;
  }
}

.avatar {
  width: 34px;
  height: 34px;
  border-radius: 10px;
  display: grid;
  place-items: center;
  font-size: 13px;
  font-weight: 700;
  color: #fff;
  flex: none;
  margin-top: 2px;
}
.avatar-user {
  background: var(--gradient);
}
.avatar-ai {
  background: linear-gradient(135deg, #0ea5e9, #22d3ee);
}
.ai-glyph {
  font-size: 11px;
  letter-spacing: 0.02em;
}

.msg-main {
  max-width: min(760px, 78%);
  min-width: 0;
}
.is-user .msg-main {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.msg-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
  font-size: 12px;
  color: var(--text-3);
}
.is-user .msg-meta {
  flex-direction: row-reverse;
}
.name {
  color: var(--text-2);
  font-weight: 600;
}
.model-tag {
  background: var(--bg-soft);
  border: 1px solid var(--border);
  padding: 1px 7px;
  border-radius: 6px;
  font-size: 11px;
}

.bubble {
  padding: 12px 16px;
  border-radius: 14px;
  font-size: 15px;
  line-height: 1.7;
  position: relative;
}
.bubble-ai {
  background: var(--panel);
  border: 1px solid var(--border);
  border-top-left-radius: 4px;
}
.bubble-user {
  background: var(--gradient);
  color: #fff;
  border-top-right-radius: 4px;
  box-shadow: 0 6px 18px rgba(99, 102, 241, 0.25);
}
.plain {
  white-space: pre-wrap;
  word-break: break-word;
}

.thinking {
  display: flex;
  gap: 5px;
  padding: 4px 2px;
}
.thinking span {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--primary);
  opacity: 0.4;
  animation: blink 1.2s infinite;
}
.thinking span:nth-child(2) {
  animation-delay: 0.2s;
}
.thinking span:nth-child(3) {
  animation-delay: 0.4s;
}
@keyframes blink {
  0%,
  60%,
  100% {
    opacity: 0.25;
    transform: translateY(0);
  }
  30% {
    opacity: 1;
    transform: translateY(-3px);
  }
}

.caret {
  display: inline-block;
  width: 7px;
  height: 16px;
  background: var(--primary);
  border-radius: 2px;
  margin-left: 3px;
  vertical-align: -2px;
  animation: caret 1s steps(1) infinite;
}
@keyframes caret {
  50% {
    opacity: 0;
  }
}

.err {
  color: var(--danger);
  font-size: 13px;
  margin-top: 6px;
}

.msg-actions {
  margin-top: 6px;
  opacity: 0;
  transition: opacity 0.15s;
}
.msg-row:hover .msg-actions {
  opacity: 1;
}
.act {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  border: 1px solid var(--border);
  background: var(--panel);
  color: var(--text-2);
  font-size: 12px;
  padding: 3px 9px;
  border-radius: 7px;
  cursor: pointer;
  font-family: inherit;
}
.act:hover {
  color: var(--primary);
  border-color: var(--primary);
}
</style>
