import { defineStore } from 'pinia'
import * as api from '@/api'

export const useChatStore = defineStore('chat', {
  state: () => ({
    models: [],
    conversations: [],
    activeId: null,
    messages: [],
    loadingMessages: false,
  }),
  getters: {
    activeConversation: (s) => s.conversations.find((c) => c.id === s.activeId) || null,
    currentModelId() {
      return this.activeConversation?.model_id || this.models[0]?.id || 'remote'
    },
    currentModel() {
      return this.models.find((m) => m.id === this.currentModelId) || null
    },
  },
  actions: {
    async loadModels() {
      const res = await api.listModels()
      this.models = res.data
      return this.models
    },
    async loadConversations() {
      const res = await api.listConversations()
      this.conversations = res.data
      return this.conversations
    },
    async createConversation(modelId) {
      const res = await api.createConversation({ model_id: modelId || this.models[0]?.id })
      this.conversations.unshift(res.data)
      this.activeId = res.data.id
      this.messages = []
      return res.data
    },
    async selectConversation(id) {
      this.activeId = id
      this.loadingMessages = true
      try {
        const res = await api.listMessages(id)
        this.messages = res.data
      } finally {
        this.loadingMessages = false
      }
    },
    async renameConversation(id, title) {
      const res = await api.patchConversation(id, { title })
      const idx = this.conversations.findIndex((c) => c.id === id)
      if (idx >= 0) this.conversations[idx] = res.data
    },
    async switchModel(modelId) {
      const id = this.activeId
      if (!id) return
      const res = await api.patchConversation(id, { model_id: modelId })
      const idx = this.conversations.findIndex((c) => c.id === id)
      if (idx >= 0) this.conversations[idx] = res.data
    },
    async removeConversation(id) {
      await api.deleteConversation(id)
      this.conversations = this.conversations.filter((c) => c.id !== id)
      if (this.activeId === id) {
        this.activeId = this.conversations[0]?.id || null
        this.messages = []
        if (this.activeId) await this.selectConversation(this.activeId)
      }
    },
  },
})
