// Thin fetch wrapper: adds the JWT, parses errors, supports file upload (form) and downloads (blob).
const BASE = import.meta.env.VITE_API_URL || '/api'

export const getToken = () => localStorage.getItem('token')

export async function api(path, { method = 'GET', body, form, blob = false } = {}) {
  const headers = {}
  const token = getToken()
  if (token) headers.Authorization = `Bearer ${token}`
  let payload
  if (form) payload = form
  else if (body !== undefined) { headers['Content-Type'] = 'application/json'; payload = JSON.stringify(body) }

  let res
  try { res = await fetch(BASE + path, { method, headers, body: payload }) }
  catch { throw new Error('Cannot reach the server. Is the backend running?') }

  if (res.status === 401 && !path.startsWith('/auth/login')) {
    localStorage.removeItem('token')
    if (!location.pathname.startsWith('/login')) location.href = '/login'
  }
  if (blob) {
    if (!res.ok) throw new Error(`Download failed (${res.status})`)
    return res.blob()
  }
  const data = await res.json().catch(() => ({}))
  if (!res.ok) throw new Error(data.error || data.msg || `Request failed (${res.status})`)
  return data
}

export function saveBlob(blob, filename) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url; a.download = filename; a.click()
  URL.revokeObjectURL(url)
}
