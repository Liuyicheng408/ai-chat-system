<script setup>
import { reactive, ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const mode = ref('login')
const loading = ref(false)
const form = reactive({ username: '', password: '', nickname: '', confirm: '' })

const isRegister = computed(() => mode.value === 'register')

function switchMode(m) {
  mode.value = m
  form.password = ''
  form.confirm = ''
}

async function submit() {
  if (!form.username || !form.password) {
    ElMessage.warning('请填写用户名和密码')
    return
  }
  if (isRegister.value) {
    if (form.username.length < 3) return ElMessage.warning('用户名至少 3 位')
    if (form.password.length < 8) return ElMessage.warning('密码至少 8 位')
    if (form.password !== form.confirm) return ElMessage.warning('两次输入的密码不一致')
  }
  if (form.password.length < 8) return ElMessage.warning('密码至少 8 位')

  loading.value = true
  try {
    if (isRegister.value) {
      await userStore.register(form.username, form.password, form.nickname || form.username)
      ElMessage.success('注册成功，正在登录…')
    }
    await userStore.login(form.username, form.password)
    await userStore.fetchMe()
    ElMessage.success('欢迎回来，' + userStore.displayName)
    router.replace(route.query.redirect || '/')
  } catch (err) {
    // 拦截器已提示
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-page">
    <div class="bg-orb orb-1"></div>
    <div class="bg-orb orb-2"></div>

    <div class="login-shell">
      <section class="brand-side">
        <div class="brand-mark">
          <span class="logo">智</span>
          <span class="brand-name">智语 Chat</span>
        </div>

        <h1 class="headline">
          一个入口<br />
          <span class="gradient-text">连接所有大模型</span>
        </h1>
        <p class="sub">
          远端 API 与本地微调模型自由切换，对话数据留在自己的服务器。
        </p>

        <ul class="features">
          <li><i class="dot"></i> 多模型实时切换，上下文无缝衔接</li>
          <li><i class="dot"></i> 支持 LoRA / 原生 pt 本地模型</li>
          <li><i class="dot"></i> 密码 RSA 加密传输 + bcrypt 存储</li>
        </ul>

        <div class="brand-foot">课程大作业 · AI 聊天对话系统</div>
      </section>

      <section class="form-side">
        <div class="form-card">
          <h2>{{ isRegister ? '创建账户' : '欢迎回来' }}</h2>
          <p class="form-sub">{{ isRegister ? '注册后即可开始对话' : '登录以继续你的对话' }}</p>

          <div class="tabs">
            <button :class="['tab', { active: !isRegister }]" @click="switchMode('login')">登录</button>
            <button :class="['tab', { active: isRegister }]" @click="switchMode('register')">注册</button>
          </div>

          <el-form @submit.prevent="submit" class="form">
            <label class="field-label">用户名</label>
            <el-input
              v-model="form.username"
              placeholder="请输入用户名"
              size="large"
              :prefix-icon="'User'"
              autocomplete="username"
            />

            <template v-if="isRegister">
              <label class="field-label">昵称（可选）</label>
              <el-input v-model="form.nickname" placeholder="别人看到的名字" size="large" />
            </template>

            <label class="field-label">密码</label>
            <el-input
              v-model="form.password"
              type="password"
              placeholder="至少 8 位"
              size="large"
              show-password
              autocomplete="current-password"
              @keyup.enter="submit"
            />

            <template v-if="isRegister">
              <label class="field-label">确认密码</label>
              <el-input
                v-model="form.confirm"
                type="password"
                placeholder="再次输入密码"
                size="large"
                show-password
                @keyup.enter="submit"
              />
            </template>

            <el-button class="submit-btn" type="primary" size="large" :loading="loading" @click="submit">
              {{ isRegister ? '注册并登录' : '登录' }}
            </el-button>
          </el-form>

          <p class="tip">
            <el-icon><Lock /></el-icon>
            密码经 RSA 公钥加密后传输，服务器仅保存哈希
          </p>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  position: relative;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  background: var(--bg);
  padding: 24px;
}

.bg-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(90px);
  opacity: 0.55;
  pointer-events: none;
}
.orb-1 {
  width: 520px;
  height: 520px;
  background: radial-gradient(circle, #6366f1, transparent 70%);
  top: -160px;
  left: -120px;
}
.orb-2 {
  width: 460px;
  height: 460px;
  background: radial-gradient(circle, #a855f7, transparent 70%);
  bottom: -180px;
  right: -100px;
}

.login-shell {
  position: relative;
  display: grid;
  grid-template-columns: 1.05fr 0.95fr;
  width: min(1040px, 100%);
  min-height: 600px;
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 24px;
  box-shadow: var(--shadow-lg);
  overflow: hidden;
}

.brand-side {
  padding: 52px 48px;
  background: linear-gradient(155deg, rgba(99, 102, 241, 0.12), rgba(168, 85, 247, 0.06) 45%, transparent);
  display: flex;
  flex-direction: column;
}

.brand-mark {
  display: flex;
  align-items: center;
  gap: 10px;
}
.logo {
  width: 38px;
  height: 38px;
  border-radius: 11px;
  display: grid;
  place-items: center;
  color: #fff;
  font-weight: 700;
  font-size: 18px;
  background: var(--gradient);
  box-shadow: 0 6px 18px rgba(99, 102, 241, 0.4);
}
.brand-name {
  font-size: 17px;
  font-weight: 650;
  letter-spacing: 0.01em;
}

.headline {
  margin: 56px 0 18px;
  font-size: 40px;
  line-height: 1.28;
  font-weight: 750;
  letter-spacing: -0.02em;
}

.sub {
  color: var(--text-2);
  font-size: 15px;
  line-height: 1.7;
  max-width: 360px;
  margin: 0;
}

.features {
  list-style: none;
  padding: 0;
  margin: 40px 0 0;
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.features li {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
  color: var(--text-2);
}
.dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--gradient);
  flex: none;
}

.brand-foot {
  margin-top: auto;
  font-size: 12px;
  color: var(--text-3);
  letter-spacing: 0.04em;
}

.form-side {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 48px 44px;
  border-left: 1px solid var(--border);
}

.form-card {
  width: 100%;
  max-width: 340px;
}
.form-card h2 {
  margin: 0 0 6px;
  font-size: 25px;
  font-weight: 700;
  letter-spacing: -0.01em;
}
.form-sub {
  margin: 0 0 24px;
  color: var(--text-2);
  font-size: 13.5px;
}

.tabs {
  display: flex;
  gap: 6px;
  background: var(--bg-soft);
  padding: 4px;
  border-radius: 11px;
  margin-bottom: 26px;
}
.tab {
  flex: 1;
  border: none;
  background: transparent;
  padding: 9px;
  border-radius: 8px;
  font-size: 14px;
  color: var(--text-2);
  cursor: pointer;
  transition: all 0.18s ease;
  font-family: inherit;
}
.tab.active {
  background: var(--panel);
  color: var(--text);
  font-weight: 600;
  box-shadow: var(--shadow-sm);
}

.field-label {
  display: block;
  font-size: 13px;
  color: var(--text-2);
  margin: 14px 0 7px;
}

.submit-btn {
  width: 100%;
  margin-top: 28px;
  height: 44px;
  border-radius: 11px;
  font-size: 15px;
  background: var(--gradient) !important;
  border: none !important;
  letter-spacing: 0.04em;
}
.submit-btn:hover {
  opacity: 0.92;
}

.tip {
  display: flex;
  align-items: center;
  gap: 6px;
  justify-content: center;
  margin-top: 22px;
  font-size: 12px;
  color: var(--text-3);
}

@media (max-width: 860px) {
  .login-shell {
    grid-template-columns: 1fr;
  }
  .brand-side {
    display: none;
  }
  .form-side {
    border-left: none;
  }
}
</style>
