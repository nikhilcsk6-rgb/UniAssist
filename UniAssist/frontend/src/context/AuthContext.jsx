import { createContext, useCallback, useContext, useEffect, useState } from 'react'
import { api } from '../api/client'

const AuthContext = createContext(null)
export const useAuth = () => useContext(AuthContext)

function applyTheme(theme) {
  document.documentElement.classList.toggle('dark', theme === 'dark')
  localStorage.setItem('theme', theme)
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(!!localStorage.getItem('token'))

  useEffect(() => {
    if (!localStorage.getItem('token')) return
    api('/auth/me').then((d) => { setUser(d.user); applyTheme(d.user.theme) })
      .catch(() => localStorage.removeItem('token')).finally(() => setLoading(false))
  }, [])

  const login = useCallback(async (email, password) => {
    const d = await api('/auth/login', { method: 'POST', body: { email, password } })
    localStorage.setItem('token', d.access_token)
    setUser(d.user); applyTheme(d.user.theme)
    return d.user
  }, [])

  const logout = useCallback(() => { localStorage.removeItem('token'); setUser(null) }, [])

  const updateProfile = useCallback(async (changes) => {
    const d = await api('/auth/me', { method: 'PUT', body: changes })
    setUser(d.user)
    if (changes.theme) applyTheme(d.user.theme)
    return d.user
  }, [])

  const toggleTheme = useCallback(() => {
    const next = document.documentElement.classList.contains('dark') ? 'light' : 'dark'
    applyTheme(next)
    if (localStorage.getItem('token')) api('/auth/me', { method: 'PUT', body: { theme: next } }).then((d) => setUser(d.user)).catch(() => {})
  }, [])

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, updateProfile, toggleTheme }}>
      {children}
    </AuthContext.Provider>
  )
}
