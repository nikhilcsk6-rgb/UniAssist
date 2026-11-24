import { useState } from 'react'
import toast from 'react-hot-toast'
import { useAuth } from '../context/AuthContext'
import { Badge, Card, Field, LangSelect, PageHeader } from '../components/ui'

export function Profile() {
  const { user, updateProfile } = useAuth()
  const [name, setName] = useState(user.full_name)
  async function save(e) {
    e.preventDefault()
    try { await updateProfile({ full_name: name }); toast.success('Profile updated') } catch (err) { toast.error(err.message) }
  }
  return (
    <>
      <PageHeader title="My Profile" />
      <Card className="max-w-xl">
        <div className="mb-4 flex items-center gap-4">
          <div className="flex h-16 w-16 items-center justify-center rounded-full bg-brand-600 text-2xl font-bold text-white" aria-hidden="true">{user.full_name[0]}</div>
          <div><p className="text-lg font-semibold">{user.full_name}</p><Badge>{user.role}</Badge></div>
        </div>
        <form onSubmit={save} className="space-y-3">
          <Field label="Full name" id="pn"><input id="pn" required className="input" value={name} onChange={(e) => setName(e.target.value)} /></Field>
          <Field label="Email" id="pe"><input id="pe" className="input" value={user.email} disabled /></Field>
          <Field label="Department" id="pd"><input id="pd" className="input" value={user.department || '-'} disabled /></Field>
          <p className="text-xs text-slate-500">Member since {user.created_at?.slice(0, 10)}</p>
          <button className="btn btn-primary">Save changes</button>
        </form>
      </Card>
    </>
  )
}

export function Settings() {
  const { user, updateProfile } = useAuth()
  const [pw, setPw] = useState({ current_password: '', new_password: '' })
  async function change(e) {
    e.preventDefault()
    try { await updateProfile(pw); toast.success('Password changed'); setPw({ current_password: '', new_password: '' }) } catch (err) { toast.error(err.message) }
  }
  const pref = (body) => updateProfile(body).then(() => toast.success('Saved')).catch((e) => toast.error(e.message))
  return (
    <>
      <PageHeader title="Settings" />
      <div className="grid max-w-4xl gap-4 md:grid-cols-2">
        <Card title="Preferences">
          <div className="space-y-4">
            <Field label="Preferred language for AI responses" id="sl"><LangSelect id="sl" value={user.preferred_language} onChange={(v) => pref({ preferred_language: v })} /></Field>
            <Field label="Theme" id="th">
              <select id="th" className="input" value={user.theme} onChange={(e) => pref({ theme: e.target.value })}><option value="light">Light</option><option value="dark">Dark</option></select>
            </Field>
          </div>
        </Card>
        <Card title="Change password">
          <form onSubmit={change} className="space-y-3">
            <Field label="Current password" id="cp"><input id="cp" type="password" required autoComplete="current-password" className="input" value={pw.current_password} onChange={(e) => setPw({ ...pw, current_password: e.target.value })} /></Field>
            <Field label="New password (8+ chars, letters and digits)" id="np"><input id="np" type="password" required minLength={8} autoComplete="new-password" className="input" value={pw.new_password} onChange={(e) => setPw({ ...pw, new_password: e.target.value })} /></Field>
            <button className="btn btn-primary">Update password</button>
          </form>
        </Card>
      </div>
    </>
  )
}
