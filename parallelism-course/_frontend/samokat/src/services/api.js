import { auth } from './auth'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'

export async function apiFetch(path, options = {}) {
  const response = await request(path, options)

  if (response.status !== 401 || !auth.refreshToken) {
    return parseResponse(response)
  }

  const refreshed = await refreshTokens()
  if (!refreshed) {
    auth.clear()
    throw new Error('Нужно войти заново')
  }

  return parseResponse(await request(path, options))
}

export function getApiError(error) {
  return error?.message || 'Что-то пошло не так'
}

async function request(path, options = {}) {
  const headers = new Headers(options.headers || {})
  const hasBody = options.body !== undefined

  if (hasBody && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }

  if (auth.accessToken) {
    headers.set('Authorization', `Bearer ${auth.accessToken}`)
  }

  return fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
    body: hasBody ? JSON.stringify(options.body) : undefined,
  })
}

async function refreshTokens() {
  const response = await fetch(`${API_BASE}/auth/refresh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: auth.refreshToken }),
  })

  if (!response.ok) return false

  auth.setTokens(await response.json())
  return true
}

async function parseResponse(response) {
  const text = await response.text()
  const data = text ? JSON.parse(text) : null

  if (!response.ok) {
    const detail = data?.detail
    throw new Error(typeof detail === 'string' ? detail : 'Ошибка запроса')
  }

  return data
}
