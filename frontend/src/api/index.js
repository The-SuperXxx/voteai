const BACKEND = 'https://occupied-vegetarian-orchestra-edge.trycloudflare.com'
const BASE = `${BACKEND}/api`

export async function askQuestion(question) {
  const res = await fetch(`${BASE}/ask`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question }),
  })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

export async function askQuestionStream(question, callbacks) {
  const { onToken, onDone, onResult, onStatus, onError, onLimit } = callbacks
  try {
    const res = await fetch(`${BASE}/ask/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question }),
    })
    if (!res.ok) {
      const text = await res.text()
      if (res.status === 429 || text.includes('limit') || text.includes('剩余')) {
        onLimit && onLimit(text)
        return
      }
      throw new Error(`HTTP ${res.status}: ${text.slice(0,100)}`)
    }
    const reader = res.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('
')
      buffer = lines.pop() || ''
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6))
            if (data.type === 'token') {
              onToken && onToken(data.model, data.token)
            } else if (data.type === 'done') {
              onDone && onDone(data.model)
            } else if (data.type === 'status') {
              onStatus && onStatus(data)
            } else if (data.type === 'result') {
              onResult && onResult(data)
            } else if (data.type === 'limit') {
              onLimit && onLimit(data.message)
            } else if (data.type === 'error') {
              onError && onError(data.error || data.model + ' 出错')
            }
          } catch {}
        }
      }
    }
  } catch (e) {
    onError && onError(e.message)
  }
}

export async function getHistory(limit = 20) {
  const res = await fetch(`${BASE}/history?limit=${limit}`)
  if (!res.ok) return { items: [] }
  return res.json()
}

export async function getResult(id) {
  const res = await fetch(`${BASE}/result/${id}`)
  if (!res.ok) return null
  return res.json()
}

export async function deleteResult(id) {
  await fetch(`${BASE}/result/${id}`, { method: 'DELETE' })
}

export async function getQuota() {
  const res = await fetch(`${BASE}/quota`)
  if (!res.ok) return { remaining: 10, limit: 10 }
  return res.json()
}