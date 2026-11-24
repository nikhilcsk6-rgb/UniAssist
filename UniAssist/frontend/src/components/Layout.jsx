import { useState } from 'react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const NAV = [
  { to: '/app', label: 'Dashboard', icon: '🏠', end: true },
  { to: '/app/chat', label: 'AI Chatbot', icon: '💬' },
  { to: '/app/documents', label: 'Document Assistant', icon: '📄' },
  { to: '/app/questions', label: 'Question Papers', icon: '📝' },
  { to: '/app/study', label: 'Study Assistant', icon: '🎓' },
  { to: '/app/quiz', label: 'Quizzes', icon: '🧠' },
  { to: '/app/announcements', label: 'Announcements', icon: '📢' },
  { to: '/app/history', label: 'Chat History', icon: '🕘' },
  { to: '/app/knowledge', label: 'Knowledge Base', icon: '📚', roles: ['admin', 'faculty'] },
  { to: '/app/users', label: 'Users & Audit', icon: '👥', roles: ['admin'] },
  { to: '/app/research', label: 'Research Analytics', icon: '📊', roles: ['admin'] },
  { to: '/app/feedback', label: 'Feedback', icon: '⭐' },
]

export default function Layout() {
  const { user, logout, toggleTheme } = useAuth()
  const nav = useNavigate()
  const [collapsed, setCollapsed] = useState(false)   // desktop: icon-only
  const [open, setOpen] = useState(false)             // mobile: drawer
  const items = NAV.filter((n) => !n.roles || n.roles.includes(user.role))

  const link = ({ isActive }) =>
    `flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition ${isActive ? 'bg-brand-600 text-white' : 'text-navy-100 hover:bg-navy-700'}`

  return (
    <div className="flex h-screen overflow-hidden">
      {open && <div className="fixed inset-0 z-30 bg-black/50 lg:hidden" onClick={() => setOpen(false)} aria-hidden="true" />}
      <aside aria-label="Sidebar"
        className={`fixed z-40 flex h-full flex-col bg-navy-900 p-3 text-white transition-all lg:static ${open ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'} ${collapsed ? 'lg:w-[72px]' : 'lg:w-64'} w-64`}>
        <div className="mb-4 flex items-center gap-2 px-2 py-2">
          <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-600 font-bold" aria-hidden="true">U</span>
          {!collapsed && <span className="text-lg font-bold">UniAssist</span>}
        </div>
        <nav className="flex-1 space-y-1 overflow-y-auto" aria-label="Main">
          {items.map((n) => (
            <NavLink key={n.to} to={n.to} end={n.end} className={link} onClick={() => setOpen(false)} title={n.label}>
              <span aria-hidden="true">{n.icon}</span>{!collapsed && n.label}
            </NavLink>
          ))}
        </nav>
        <div className="space-y-1 border-t border-navy-700 pt-2">
          <NavLink to="/app/profile" className={link} onClick={() => setOpen(false)}><span aria-hidden="true">👤</span>{!collapsed && 'Profile'}</NavLink>
          <NavLink to="/app/settings" className={link} onClick={() => setOpen(false)}><span aria-hidden="true">⚙️</span>{!collapsed && 'Settings'}</NavLink>
          <button onClick={() => { logout(); nav('/login') }} className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-navy-100 hover:bg-navy-700">
            <span aria-hidden="true">🚪</span>{!collapsed && 'Log out'}
          </button>
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center justify-between border-b border-slate-200 bg-white px-4 py-3 dark:border-navy-700 dark:bg-navy-900">
          <div className="flex items-center gap-2">
            <button className="btn btn-ghost !px-3 lg:hidden" onClick={() => setOpen(true)} aria-label="Open menu">☰</button>
            <button className="btn btn-ghost hidden !px-3 lg:inline-flex" onClick={() => setCollapsed(!collapsed)} aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}>
              {collapsed ? '»' : '«'}
            </button>
          </div>
          <div className="flex items-center gap-3">
            <button className="btn btn-ghost !px-3" onClick={toggleTheme} aria-label="Toggle light or dark mode">🌓</button>
            <div className="text-right text-sm leading-tight">
              <div className="font-semibold text-navy-900 dark:text-white">{user.full_name}</div>
              <div className="text-xs capitalize text-brand-600 dark:text-brand-300">{user.role}</div>
            </div>
          </div>
        </header>
        <main className="flex-1 overflow-y-auto p-4 md:p-6"><Outlet /></main>
      </div>
    </div>
  )
}
