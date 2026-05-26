const BASE = '/api'

export async function askQuestion(question) {
  const res = await fetch(`${BASE}/ask`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question }),
  })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

export function askQuestionStream(question, callbacks) {
  const { onToken, onDone, onStatus, onResult, onError, onLimit } = callbacks

  fetch(`${BASE}/ask/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question }),
  }).then(async (response) => {
    if (!response.ok) throw new Error(`HTTP ${response.status}`)
    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
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
              onStatus && onStatus(data.status)
            } else if (data.type === 'result') {
              onResult && onResult(data)
            } else if (data.type === 'limit') {
              onLimit && onLimit(data.message)
            } else if (data.type === 'error') {
              onError && onError(data.error || data.model + ' 出错')
            }
          } catch (e) {
            // skip parse errors
          }
        }
      }
    }
  }).catch(err => {
    onError && onError(err.message)
  })
}

export async function getHistory(limit = 20) {
  const res = await fetch(`${BASE}/history?limit=${limit}`)
  return res.json()
}

export async function getResult(id) {
  const res = await fetch(`${BASE}/result/${id}`)
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

export async function deleteResult(id) {
  await fetch(`${BASE}/result/${id}`, { method: 'DELETE' })
}

export async function getQuota() {
  const res = await fetch(`${BASE}/quota`)
  return res.json()
}
