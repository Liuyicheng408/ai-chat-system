<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'
import { changePassword, getPublicKey } from '@/api'
import { encryptPassword } from '@/utils/crypto'

const router = useRouter()
const userStore = useUserStore()

const saving = ref(false)
const changing = ref(false)
const profile = reactive({ nickname: '', email: '', avatar: '', bio: '' })
const pwd = reactive({ old: '', next: '', confirm: '' })

const avatars = ['🧑‍🎓', '👩‍💻', '👨‍💻', '🦊', '🐼', '🚀', '🌙', '⭐', '🎧', '🍀']

onMounted(async () => {
  if (!userStore.user) {
    try { await userStore.fetchMe() } catch (e) { /* ignore */ }
  }
  if (userStore.user) {
    profile.nickname = userStore.user.nickname || ''
    profile.email = userStore.user.email || ''
    profile.avatar = userStore.user.avatar || ''
    profile.bio = userStore.user.bio || ''
  }
})

async function saveProfile() {
  saving.value = true
  try {
    await userStore.saveProfile({
      nickname: profile.nickname,
      email: profile.email || null,
      avatar: profile.avatar,
      bio: profile.bio,
    })
    ElMessage.success('资料已保存')
  } catch (e) { /* ignore */ } finally {
    saving.value = false
  }
}

async function submitPassword() {
  if (!pwd.old || !pwd.next) return ElMessage.warning('请填写完整')
  if (pwd.next.length < 8) return ElMessage.warning('新密码至少 8 位')
  if (!/[A-Za-z]/.test(pwd.next) || !/\d/.test(pwd.next)) return ElMessage.warning('新密码需包含字母和数字')
  if (pwd.next !== pwd.confirm) return ElMessage.warning('两次输入的新密码不一致')

  changing.value = true
  try {
    const pem = (await getPublicKey()).data.public_key
    const res = await changePassword({
      old_password: await encryptPassword(pwd.old, pem),
      new_password: await encryptPassword(pwd.next, pem),
    })
    if (res.data?.token) userStore.setToken(res.data.token)
    ElMessage.success('密码已修改，其他设备需重新登录')
    pwd.old = ''
    pwd.next = ''
    pwd.confirm = ''
  } catch (e) { /* ignore */ } finally {
    changing.value = false
  }
}

function pickAvatar(a) {
  profile.avatar = a
}
</script>

<template>
  <div class="profile-page">
    <header class="page-head">
      <button class="back" @click="router.push('/')">
        <el-icon><ArrowLeft /></el-icon>返回对话
      </button>
      <h1>个人中心</h1>
      <div class="head-right">
        <el-button text @click="userStore.toggleTheme()">
          <el-icon><Moon /></el-icon>
        </el-button>
      </div>
    </header>

    <main class="content">
      <section class="card">
        <div class="card-head">
          <h2>基本资料</h2>
          <p>这些信息会显示在聊天界面中</p>
        </div>

        <div class="profile-top">
          <div class="big-avatar">{{ profile.avatar || userStore.initial }}</div>
          <div class="avatar-picker">
            <span class="picker-label">选择头像</span>
            <div class="avatar-list">
              <button
                v-for="a in avatars"
                :key="a"
                :class="['avatar-opt', { on: profile.avatar === a }]"
                @click="pickAvatar(a)"
              >
                {{ a }}
              </button>
            </div>
          </div>
        </div>

        <div class="grid">
          <div class="field">
            <label>昵称</label>
            <el-input v-model="profile.nickname" maxlength="30" placeholder="怎么称呼你" />
          </div>
          <div class="field">
            <label>邮箱</label>
            <el-input v-model="profile.email" placeholder="you@example.com" />
          </div>
          <div class="field full">
            <label>个性签名</label>
            <el-input v-model="profile.bio" maxlength="255" placeholder="一句话介绍自己" />
          </div>
        </div>

        <div class="card-foot">
          <span class="meta">用户名：{{ userStore.user?.username }}</span>
          <el-button type="primary" :loading="saving" @click="saveProfile">保存修改</el-button>
        </div>
      </section>

      <section class="card">
        <div class="card-head">
          <h2>修改密码</h2>
          <p>密码以 RSA 加密传输，服务器只保存 bcrypt 哈希</p>
        </div>

        <div class="grid">
          <div class="field full">
            <label>当前密码</label>
            <el-input v-model="pwd.old" type="password" show-password placeholder="请输入原密码" />
          </div>
          <div class="field">
            <label>新密码</label>
            <el-input v-model="pwd.next" type="password" show-password placeholder="至少 8 位，含字母和数字" />
          </div>
          <div class="field">
            <label>确认新密码</label>
            <el-input v-model="pwd.confirm" type="password" show-password placeholder="再次输入新密码" />
          </div>
        </div>

        <div class="card-foot">
          <span class="meta">修改成功后其他设备会被强制下线</span>
          <el-button type="primary" :loading="changing" @click="submitPassword">确认修改</el-button>
        </div>
      </section>
    </main>
  </div>
</template>

<style scoped>
.profile-page {
  min-height: 100vh;
  background: var(--bg);
}
.page-head {
  display: flex;
  align-items: center;
  gap: 18px;
  padding: 0 28px;
  height: 64px;
  background: var(--panel);
  border-bottom: 1px solid var(--border);
  position: sticky;
  top: 0;
  z-index: 10;
}
.back {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  border: 1px solid var(--border);
  background: var(--panel);
  color: var(--text-2);
  padding: 7px 12px;
  border-radius: 9px;
  cursor: pointer;
  font-size: 13px;
  font-family: inherit;
}
.back:hover {
  color: var(--primary);
  border-color: var(--primary);
}
.page-head h1 {
  font-size: 17px;
  margin: 0;
  font-weight: 650;
}
.head-right {
  margin-left: auto;
}

.content {
  max-width: 860px;
  margin: 0 auto;
  padding: 28px 24px 60px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.card {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 24px 26px;
  box-shadow: var(--shadow-sm);
}
.card-head h2 {
  margin: 0 0 4px;
  font-size: 16px;
  font-weight: 650;
}
.card-head p {
  margin: 0 0 20px;
  color: var(--text-3);
  font-size: 12.5px;
}

.profile-top {
  display: flex;
  align-items: center;
  gap: 22px;
  padding: 4px 0 22px;
  border-bottom: 1px dashed var(--border);
  margin-bottom: 20px;
}
.big-avatar {
  width: 64px;
  height: 64px;
  border-radius: 18px;
  background: var(--gradient);
  color: #fff;
  display: grid;
  place-items: center;
  font-size: 26px;
  font-weight: 700;
  flex: none;
  box-shadow: 0 10px 24px rgba(99, 102, 241, 0.3);
}
.picker-label {
  font-size: 12px;
  color: var(--text-3);
  display: block;
  margin-bottom: 8px;
}
.avatar-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.avatar-opt {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  border: 1px solid var(--border);
  background: var(--bg-soft);
  font-size: 18px;
  cursor: pointer;
  transition: all 0.15s;
}
.avatar-opt:hover {
  transform: translateY(-2px);
  border-color: var(--primary);
}
.avatar-opt.on {
  border-color: var(--primary);
  background: rgba(99, 102, 241, 0.12);
}

.grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}
.field.full {
  grid-column: 1 / -1;
}
.field label {
  display: block;
  font-size: 12.5px;
  color: var(--text-2);
  margin-bottom: 7px;
}

.card-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 22px;
  padding-top: 18px;
  border-top: 1px dashed var(--border);
}
.meta {
  font-size: 12px;
  color: var(--text-3);
}

@media (max-width: 700px) {
  .grid {
    grid-template-columns: 1fr;
  }
  .profile-top {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
