import { defineStore } from 'pinia'
import { getPublicKey, login as apiLogin, register as apiRegister, getMe, updateMe } from '@/api'
import { encryptPassword } from '@/utils/crypto'

export const useUserStore = defineStore('user', {
  state: () => ({
    token: localStorage.getItem('token') || '',
    user: null,
    theme: localStorage.getItem('theme') || 'light',
  }),
  getters: {
    displayName: (s) => s.user?.nickname || s.user?.username || '未登录',
    initial: (s) => (s.user?.nickname || s.user?.username || 'U').slice(0, 1).toUpperCase(),
  },
  actions: {
    async fetchPublicKey() {
      const res = await getPublicKey()
      return res.data.public_key
    },
    async login(username, password) {
      const pem = await this.fetchPublicKey()
      const encrypted = await encryptPassword(password, pem)
      const res = await apiLogin({ username, password: encrypted })
      this.token = res.data.token
      this.user = res.data.user
      localStorage.setItem('token', this.token)
      return res
    },
    async register(username, password, nickname) {
      const pem = await this.fetchPublicKey()
      const encrypted = await encryptPassword(password, pem)
      return apiRegister({ username, password: encrypted, nickname })
    },
    async fetchMe() {
      const res = await getMe()
      this.user = res.data
      return this.user
    },
    async saveProfile(payload) {
      const res = await updateMe(payload)
      this.user = res.data
      return res
    },
    logout() {
      this.token = ''
      this.user = null
      localStorage.removeItem('token')
    },
    setToken(token) {
      this.token = token
      localStorage.setItem('token', token)
    },
    toggleTheme() {
      this.theme = this.theme === 'dark' ? 'light' : 'dark'
      localStorage.setItem('theme', this.theme)
      this.applyTheme()
    },
    applyTheme() {
      const el = document.documentElement
      if (this.theme === 'dark') el.classList.add('dark')
      else el.classList.remove('dark')
    },
  },
})
