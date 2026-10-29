import { API_BASE } from './http'

/**
 * POST + 流式读取 SSE（EventSource 不支持自定义 Header 与 POST，故用 fetch）
 */
export async function streamChat(payload, { onEvent, signal, onError } = {}) {
  const token = localStorage.getItem('token')
  let res
  try {
    res = await fetch(API_BASE + '/api/chat/stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: 'Bearer ' + token,
      },
      body: JSON.stringify(payload),
      signal,
    })
  } catch (err) {
    if (err.name === 'AbortError') return
    onError && onError(err)
    return
  }

  if (!res.ok) {
    let msg = 'HTTP ' + res.status
    try {
      const body = await res.json()
      msg = body.message || msg
    } catch (e) { /* ignore */ }
    onError && onError(new Error(msg))
    return
  }

  const reader = res.body.getReader()
  const decoder = new TextDecoder('utf-8')
  let buffer = ''

  while (true) {
    let chunk
    try {
      chunk = await reader.read()
    } catch (err) {
      if (err.name !== 'AbortError') onError && onError(err)
      break
    }
    if (chunk.done) break
    buffer += decoder.decode(chunk.value, { stream: true })
    const parts = buffer.split('\n\n')
    buffer = parts.pop()
    for (const part of parts) {
      const line = part.split('\n').find((l) => l.startsWith('data:'))
      if (!line) continue
      const raw = line.slice(5).trim()
      if (!raw) continue
      try {
        onEvent && onEvent(JSON.parse(raw))
      } catch (e) {
        console.warn('SSE 解析失败', raw)
      }
    }
  }
}
