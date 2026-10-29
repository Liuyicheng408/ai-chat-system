<script setup>
import { computed, nextTick, onMounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useChatStore } from '@/stores/chat'
import { useUserStore } from '@/stores/user'
import { streamChat } from '@/api/stream'
import MessageItem from '@/components/MessageItem.vue'
import ModelSelect from '@/components/ModelSelect.vue'

const router = useRouter()
const store = useChatStore()
const userStore = useUserStore()

const draft = ref('')
const sending = ref(false)
const statusText = ref('')
const scrollRef = ref(null)
const inputRef = ref(null)
const editingId = ref(null)
const editingTitle = ref('')
let controller = null

const suggestions = [
  '用通俗的话解释一下什么是 LoRA 微调',
  '帮我写一个 Python 的快排实现，并加注释',
  '对比一下 Transformer 和 RNN 的优缺点',
]

const canSend = computed(() => draft.value.trim().length > 0 && !sending.value)

function fmtTime(raw) {
  if (!raw) return ''
  const d = new Date(raw)
  const diff = (Date.now() - d.getTime()) / 1000
  if (diff < 60) return '刚刚'
  if (diff < 3600) return Math.floor(diff / 60) + ' 分钟前'
  if (diff < 86400) return Math.floor(diff / 3600) + ' 小时前'
  if (diff < 86400 * 2) return '昨天'
  return d.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' })
}

function scrollToBottom(smooth) {
  const el = scrollRef.value
  if (!el) return
  el.scrollTo({ top: el.scrollHeight, behavior: smooth ? 'smooth' : 'auto' })
}

onMounted(async () => {
  if (!userStore.user) {
    try { await userStore.fetchMe() } catch (e) { /* ignore */ }
  }
  try {
    await store.loadModels()
    await store.loadConversations()
    if (store.conversations.length) {
      await store.selectConversation(store.conversations[0].id)
      await nextTick()
      scrollToBottom(false)
    }
  } catch (e) { /* 拦截器已提示 */ }
})

async function onNewChat() {
  try {
    await store.createConversation(store.currentModelId)
    draft.value = ''
    await nextTick()
    inputRef.value?.focus()
  } catch (e) { /* ignore */ }
}

async function onSelect(id) {
  if (editingId.value) return
  if (id === store.activeId) return
  await store.selectConversation(id)
  await nextTick()
  scrollToBottom(false)
}

function startRename(c) {
  editingId.value = c.id
  editingTitle.value = c.title
  nextTick(() => {
    const input = document.querySelector('.conv-rename input')
    input && input.focus()
  })
}

async function commitRename(c) {
  const title = editingTitle.value.trim()
  editingId.value = null
  if (!title || title === c.title) return
  try {
    await store.renameConversation(c.id, title)
    ElMessage.success('已重命名')
  } catch (e) { /* ignore */ }
}

async function onCommand(cmd, c) {
  if (cmd === 'rename') startRename(c)
  if (cmd === 'delete') {
    try {
      await ElMessageBox.confirm('删除后该会话的全部消息将不可恢复，确定删除「' + c.title + '」吗？', '删除会话', {
        type: 'warning',
        confirmButtonText: '删除',
        cancelButtonText: '取消',
      })
      await store.removeConversation(c.id)
      ElMessage.success('已删除')
    } catch (e) { /* 取消 */ }
  }
}

async function onModelChange(id) {
  if (!store.activeId) {
    store.models = store.models
    return
  }
  try {
    await store.switchModel(id)
    ElMessage.success('已切换模型：' + (store.models.find((m) => m.id === id)?.name || id))
  } catch (e) { /* ignore */ }
}

function modelLabel(id) {
  if (!id) return ''
  const m = store.models.find((x) => x.id === id)
  return m ? m.name : id
}

function useSuggestion(text) {
  draft.value = text
  inputRef.value?.focus()
}

async function send() {
  if (!canSend.value) return
  const text = draft.value.trim()
  if (!store.activeId) {
    await store.createConversation(store.currentModelId)
  }
  const modelId = store.currentModelId
  draft.value = ''
  statusText.value = ''

  store.messages.push({
    id: 'local-u-' + Date.now(),
    role: 'user',
    content: text,
    created_at: new Date().toISOString(),
  })
  const bot = reactive({
    id: 'local-a-' + Date.now(),
    role: 'assistant',
    content: '',
    model_id: modelId,
    created_at: new Date().toISOString(),
    streaming: true,
    error: '',
  })
  store.messages.push(bot)
  await nextTick()
  scrollToBottom(true)

  sending.value = true
  controller = new AbortController()
  const convId = store.activeId

  try {
    await streamChat(
      { conversation_id: convId, content: text, model_id: modelId },
      {
        signal: controller.signal,
        onEvent(evt) {
          if (evt.type === 'delta') {
            bot.content += evt.content
            nextTick(() => scrollToBottom(false))
          } else if (evt.type === 'status') {
            statusText.value = evt.message
          } else if (evt.type === 'error') {
            bot.error = evt.message
            statusText.value = ''
          } else if (evt.type === 'start') {
            bot.id = evt.message_id
          } else if (evt.type === 'done') {
            bot.id = evt.message_id
            statusText.value = ''
          }
        },
        onError(err) {
          bot.error = err.message
        },
      },
    )
  } finally {
    bot.streaming = false
    sending.value = false
    statusText.value = ''
    controller = null
    await refreshConversations()
    await nextTick()
    scrollToBottom(false)
  }
}

async function refreshConversations() {
  try {
    await store.loadConversations()
  } catch (e) { /* ignore */ }
}

function stop() {
  if (controller) controller.abort()
}

function onKeydown(e) {
  if (e.key === 'Enter' && !e.shiftKey && !e.isComposing) {
    e.preventDefault()
    send()
  }
}

function onUserCommand(cmd) {
  if (cmd === 'profile') router.push('/profile')
  if (cmd === 'theme') userStore.toggleTheme()
  if (cmd === 'logout') {
    userStore.logout()
    router.replace('/login')
  }
}

watch(
  () => store.activeId,
  async () => {
    await nextTick()
    scrollToBottom(false)
  },
)
</script>

<template>
  <div class="chat-page">
    <aside class="sidebar">
      <div class="brand">
        <span class="logo">智</span>
        <div class="brand-text">
          <div class="brand-name">智语 Chat</div>
          <div class="brand-sub">多模型对话</div>
        </div>
      </div>

      <button class="new-chat" @click="onNewChat">
        <el-icon><Plus /></el-icon>
        <span>新建对话</span>
      </button>

      <div class="conv-scroll">
        <div class="conv-label">最近对话</div>
        <div
          v-for="c in store.conversations"
          :key="c.id"
          :class="['conv-item', { active: c.id === store.activeId }]"
          @click="onSelect(c.id)"
        >
          <div class="conv-main">
            <el-input
              v-if="editingId === c.id"
              v-model="editingTitle"
              class="conv-rename"
              size="small"
              @click.stop
              @blur="commitRename(c)"
              @keyup.enter="commitRename(c)"
              @keydown.esc="editingId = null"
            />
            <template v-else>
              <div class="conv-title">{{ c.title }}</div>
              <div class="conv-meta">
                <span>{{ fmtTime(c.updated_at) }}</span>
                <span class="conv-model">{{ c.model_id === 'remote' ? 'API' : '本地' }}</span>
              </div>
            </template>
          </div>

          <el-dropdown trigger="click" @command="(cmd) => onCommand(cmd, c)" @click.stop>
            <span class="conv-more" @click.stop>
              <el-icon><MoreFilled /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="rename">
                  <el-icon><EditPen /></el-icon>重命名
                </el-dropdown-item>
                <el-dropdown-item command="delete" divided>
                  <el-icon><Delete /></el-icon>删除
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>

        <div v-if="!store.conversations.length" class="conv-empty">
          <el-icon><ChatDotRound /></el-icon>
          <p>还没有对话，点击上方新建</p>
        </div>
      </div>

      <div class="user-bar">
        <div class="user-avatar">{{ userStore.initial }}</div>
        <div class="user-info">
          <div class="user-name">{{ userStore.displayName }}</div>
          <div class="user-role">已登录</div>
        </div>
        <el-dropdown trigger="click" @command="onUserCommand">
          <span class="user-more"><el-icon><Setting /></el-icon></span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="profile">
                <el-icon><User /></el-icon>个人中心
              </el-dropdown-item>
              <el-dropdown-item command="theme">
                <el-icon><Moon /></el-icon>{{ userStore.theme === 'dark' ? '切换浅色' : '切换深色' }}
              </el-dropdown-item>
              <el-dropdown-item command="logout" divided>
                <el-icon><SwitchButton /></el-icon>退出登录
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </aside>

    <main class="main">
      <header class="topbar">
        <div class="top-title">
          <span class="dot-live"></span>
          {{ store.activeConversation?.title || '新对话' }}
        </div>
        <div class="top-actions">
          <ModelSelect :model-value="store.currentModelId" :models="store.models" @change="onModelChange" />
        </div>
      </header>

      <section ref="scrollRef" class="messages">
        <div v-if="!store.messages.length" class="empty-state">
          <div class="empty-orb"><span>智</span></div>
          <h2>开始一段新的对话</h2>
          <p>已接入 {{ store.models.length }} 个模型，可随时在右上角切换</p>
          <div class="suggest-list">
            <button v-for="(s, i) in suggestions" :key="i" class="suggest" @click="useSuggestion(s)">
              {{ s }}
            </button>
          </div>
        </div>

        <div v-else class="msg-list">
          <MessageItem
            v-for="m in store.messages"
            :key="m.id"
            :message="m"
            :user-name="userStore.displayName"
            :user-initial="userStore.initial"
            :model-name="modelLabel(m.model_id)"
          />
        </div>
      </section>

      <footer class="composer">
        <transition name="fade">
          <div v-if="statusText" class="status-pill">
            <span class="spin"></span>{{ statusText }}
          </div>
        </transition>

        <div class="composer-box">
          <el-input
            ref="inputRef"
            v-model="draft"
            type="textarea"
            :autosize="{ minRows: 1, maxRows: 6 }"
            resize="none"
            placeholder="输入消息，Enter 发送，Shift + Enter 换行"
            class="composer-input"
            @keydown="onKeydown"
          />
          <div class="composer-bar">
            <div class="hint">
              <el-icon><InfoFilled /></el-icon>
              <span>{{ draft.length }}/20000</span>
            </div>
            <div class="actions">
              <el-button v-if="sending" class="stop-btn" @click="stop">
                <el-icon><VideoPause /></el-icon>停止
              </el-button>
              <el-button v-else class="send-btn" type="primary" :disabled="!canSend" @click="send">
                发送<el-icon class="send-icon"><Promotion /></el-icon>
              </el-button>
            </div>
          </div>
        </div>
        <p class="disclaimer">AI 生成内容仅供参考，请自行核实关键信息。</p>
      </footer>
    </main>
  </div>
</template>

<style scoped>
.chat-page {
  display: flex;
  height: 100vh;
  background: var(--bg);
  overflow: hidden;
}

/* ---------- 侧栏 ---------- */
.sidebar {
  width: 268px;
  flex: none;
  background: var(--panel);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  padding: 18px 14px 14px;
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 4px 6px 18px;
}
.logo {
  width: 36px;
  height: 36px;
  border-radius: 11px;
  display: grid;
  place-items: center;
  color: #fff;
  font-weight: 700;
  background: var(--gradient);
  box-shadow: 0 6px 16px rgba(99, 102, 241, 0.35);
}
.brand-name {
  font-size: 15px;
  font-weight: 680;
  letter-spacing: 0.01em;
}
.brand-sub {
  font-size: 11.5px;
  color: var(--text-3);
  margin-top: 1px;
}

.new-chat {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 7px;
  width: 100%;
  padding: 11px;
  border: none;
  border-radius: 11px;
  background: var(--gradient);
  color: #fff;
  font-size: 14px;
  font-weight: 550;
  font-family: inherit;
  cursor: pointer;
  box-shadow: 0 6px 18px rgba(99, 102, 241, 0.28);
  transition: transform 0.15s, box-shadow 0.15s;
}
.new-chat:hover {
  transform: translateY(-1px);
  box-shadow: 0 9px 22px rgba(99, 102, 241, 0.38);
}
.new-chat:active {
  transform: translateY(0);
}

.conv-scroll {
  flex: 1;
  overflow-y: auto;
  margin-top: 18px;
  padding-right: 2px;
}
.conv-label {
  font-size: 11px;
  color: var(--text-3);
  letter-spacing: 0.06em;
  padding: 0 8px 8px;
  text-transform: uppercase;
}

.conv-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 9px 10px;
  border-radius: 10px;
  cursor: pointer;
  transition: background 0.15s;
  margin-bottom: 2px;
  border: 1px solid transparent;
}
.conv-item:hover {
  background: var(--bg-soft);
}
.conv-item.active {
  background: rgba(99, 102, 241, 0.1);
  border-color: rgba(99, 102, 241, 0.22);
}
.conv-main {
  flex: 1;
  min-width: 0;
}
.conv-title {
  font-size: 13.5px;
  color: var(--text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.conv-item.active .conv-title {
  font-weight: 600;
  color: var(--primary);
}
.conv-meta {
  display: flex;
  gap: 8px;
  font-size: 11px;
  color: var(--text-3);
  margin-top: 2px;
}
.conv-model {
  opacity: 0.85;
}
.conv-more {
  opacity: 0;
  color: var(--text-3);
  padding: 4px;
  border-radius: 6px;
  transition: opacity 0.15s;
}
.conv-item:hover .conv-more,
.conv-item.active .conv-more {
  opacity: 1;
}
.conv-more:hover {
  background: var(--panel-2);
  color: var(--text);
}
.conv-rename {
  width: 100%;
}

.conv-empty {
  text-align: center;
  color: var(--text-3);
  padding: 40px 10px;
  font-size: 13px;
}
.conv-empty .el-icon {
  font-size: 26px;
  margin-bottom: 8px;
}

.user-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px;
  border-radius: 12px;
  background: var(--bg-soft);
  margin-top: 10px;
}
.user-avatar {
  width: 32px;
  height: 32px;
  border-radius: 9px;
  background: var(--gradient);
  color: #fff;
  display: grid;
  place-items: center;
  font-size: 13px;
  font-weight: 700;
  flex: none;
}
.user-info {
  flex: 1;
  min-width: 0;
}
.user-name {
  font-size: 13px;
  font-weight: 550;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.user-role {
  font-size: 11px;
  color: var(--text-3);
}
.user-more {
  color: var(--text-3);
  cursor: pointer;
  padding: 4px;
}
.user-more:hover {
  color: var(--primary);
}

/* ---------- 主区 ---------- */
.main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  background: var(--bg);
}

.topbar {
  height: 62px;
  flex: none;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 22px;
  border-bottom: 1px solid var(--border);
  background: var(--panel);
}
.top-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14.5px;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.dot-live {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--success);
  box-shadow: 0 0 0 3px rgba(34, 197, 94, 0.15);
}

.messages {
  flex: 1;
  overflow-y: auto;
  padding: 26px 22px 10px;
  scroll-behavior: smooth;
}
.msg-list {
  max-width: 900px;
  margin: 0 auto;
}

.empty-state {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding-bottom: 40px;
}
.empty-orb {
  width: 74px;
  height: 74px;
  border-radius: 22px;
  background: var(--gradient);
  display: grid;
  place-items: center;
  color: #fff;
  font-size: 30px;
  font-weight: 700;
  box-shadow: 0 18px 40px rgba(99, 102, 241, 0.35);
  margin-bottom: 22px;
}
.empty-state h2 {
  margin: 0 0 8px;
  font-size: 22px;
  font-weight: 700;
  letter-spacing: -0.01em;
}
.empty-state p {
  color: var(--text-2);
  font-size: 13.5px;
  margin: 0 0 28px;
}
.suggest-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  justify-content: center;
  max-width: 640px;
}
.suggest {
  padding: 10px 16px;
  border-radius: 11px;
  border: 1px solid var(--border);
  background: var(--panel);
  color: var(--text-2);
  font-size: 13px;
  font-family: inherit;
  cursor: pointer;
  transition: all 0.16s;
}
.suggest:hover {
  color: var(--primary);
  border-color: var(--primary);
  transform: translateY(-1px);
  box-shadow: var(--shadow-sm);
}

/* ---------- 输入区 ---------- */
.composer {
  flex: none;
  padding: 10px 22px 16px;
}
.composer-box {
  max-width: 900px;
  margin: 0 auto;
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 10px 12px 8px;
  box-shadow: var(--shadow-sm);
  transition: border-color 0.15s, box-shadow 0.15s;
}
.composer-box:focus-within {
  border-color: rgba(99, 102, 241, 0.5);
  box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.08);
}
.composer-input :deep(.el-textarea__inner) {
  border: none;
  box-shadow: none;
  padding: 6px 4px;
  background: transparent;
  font-size: 14.5px;
  line-height: 1.7;
}
.composer-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 6px;
}
.hint {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 11.5px;
  color: var(--text-3);
}
.send-btn {
  background: var(--gradient) !important;
  border: none !important;
  border-radius: 9px;
  padding: 8px 18px;
  font-weight: 550;
}
.send-btn:disabled {
  opacity: 0.45;
}
.send-icon {
  margin-left: 4px;
}
.stop-btn {
  border-radius: 9px;
}
.disclaimer {
  text-align: center;
  font-size: 11px;
  color: var(--text-3);
  margin: 8px 0 0;
}

.status-pill {
  max-width: 900px;
  margin: 0 auto 8px;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: rgba(99, 102, 241, 0.1);
  color: var(--primary);
  font-size: 12px;
  padding: 6px 12px;
  border-radius: 999px;
}
.spin {
  width: 11px;
  height: 11px;
  border: 2px solid rgba(99, 102, 241, 0.25);
  border-top-color: var(--primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@media (max-width: 820px) {
  .sidebar {
    width: 76px;
    padding: 16px 8px;
  }
  .brand-text,
  .new-chat span,
  .conv-label,
  .conv-title,
  .conv-meta,
  .user-info {
    display: none;
  }
  .new-chat {
    padding: 11px 0;
  }
  .conv-item {
    justify-content: center;
  }
  .topbar {
    padding: 0 14px;
  }
}
</style>
