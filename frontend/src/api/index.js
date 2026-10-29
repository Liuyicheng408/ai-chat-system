import http from './http'

export const getPublicKey = () => http.get('/api/auth/public-key')
export const register = (data) => http.post('/api/auth/register', data)
export const login = (data) => http.post('/api/auth/login', data)

export const getMe = () => http.get('/api/users/me')
export const updateMe = (data) => http.put('/api/users/me', data)
export const changePassword = (data) => http.put('/api/users/me/password', data)

export const listConversations = () => http.get('/api/conversations')
export const createConversation = (data) => http.post('/api/conversations', data || {})
export const patchConversation = (id, data) => http.patch('/api/conversations/' + id, data)
export const deleteConversation = (id) => http.delete('/api/conversations/' + id)
export const listMessages = (id) => http.get('/api/conversations/' + id + '/messages')

export const listModels = () => http.get('/api/models')
export const loadModel = (id) => http.post('/api/models/' + id + '/load')
