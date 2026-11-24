import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import { api } from '../api/client'
import { useAuth } from '../context/AuthContext'
import { Field, Spinner } from '../components/ui'

function Shell({ title, children }) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-navy-900 to-navy-700 p-4">
      <div className="w-full max-w-md rounded-2xl bg-white p-8 shadow-2xl animate-fadeUp dark:bg-navy-900">
        <Link to="/" className="mb-4 flex items-center gap-2 text-lg font-bold text-navy-900 dark:text-white">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-600 text-white" aria-hidden="true">U</span>UniAssist
        </Link>
        <h1 className="mb-5 text-2xl font-bold text-navy-900 dark:text-white">{title}</h1>
        {children}
      </div>
    </div>
  )
}

const DEMOS = [['Student', 'student@uniassist.edu', 'Student@123'], ['Faculty', 'faculty@uniassist.edu', 'Faculty@123'], ['Admin', 'admin@uniassist.edu', 'Admin@123']]

export function Login() {
  const { login } = useAuth()
  const nav = useNavigate()
  const [form, setForm] = useState({ email: '', password: '' })
  const [busy, setBusy] = useState(false)

  async function submit(e) {
    e.preventDefault(); setBusy(true)
    try { await login(form.email, form.password); nav('/app') }
    catch (err) { toast.error(err.message) }
    finally { setBusy(false) }
  }
  return (
    <Shell title="Welcome back">
      <form onSubmit={submit} className="space-y-4">
        <Field label="Email" id="email"><input id="email" type="email" required autoComplete="email" className="input" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} /></Field>
        <Field label="Password" id="password"><input id="password" type="password" required autoComplete="current-password" className="input" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} /></Field>
        <button className="btn btn-primary w-full" disabled={busy}>{busy ? <Spinner label="Signing in..." /> : 'Log in'}</button>
      </form>
      <div className="mt-5 rounded-xl bg-slate-50 p-3 text-xs dark:bg-navy-800">
        <p className="mb-2 font-semibold">Demo accounts (click to fill)</p>
        <div className="flex gap-2">
          {DEMOS.map(([r, e, p]) => <button key={r} type="button" className="btn btn-ghost !px-3 !py-1 text-xs" onClick={() => setForm({ email: e, password: p })}>{r}</button>)}
        </div>
      </div>
      <p className="mt-4 text-sm">New here? <Link className="font-semibold text-brand-600" to="/register">Create an account</Link></p>
    </Shell>
  )
}

export function Register() {
  const nav = useNavigate()
  const [f, setF] = useState({ full_name: '', email: '', password: '', role: 'student', department: '' })
  const [busy, setBusy] = useState(false)
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value })

  async function submit(e) {
    e.preventDefault(); setBusy(true)
    try { await api('/auth/register', { method: 'POST', body: f }); toast.success('Account created. Please log in.'); nav('/login') }
    catch (err) { toast.error(err.message) }
    finally { setBusy(false) }
  }
  return (
    <Shell title="Create your account">
      <form onSubmit={submit} className="space-y-4">
        <Field label="Full name" id="name"><input id="name" required className="input" value={f.full_name} onChange={set('full_name')} /></Field>
        <Field label="Email" id="remail"><input id="remail" type="email" required className="input" value={f.email} onChange={set('email')} /></Field>
        <Field label="Password (8+ characters, letters and digits)" id="rpass"><input id="rpass" type="password" required minLength={8} autoComplete="new-password" className="input" value={f.password} onChange={set('password')} /></Field>
        <div className="grid grid-cols-2 gap-3">
          <Field label="I am a" id="role"><select id="role" className="input" value={f.role} onChange={set('role')}><option value="student">Student</option><option value="faculty">Faculty</option></select></Field>
          <Field label="Department" id="dept"><input id="dept" className="input" value={f.department} onChange={set('department')} /></Field>
        </div>
        <button className="btn btn-primary w-full" disabled={busy}>{busy ? <Spinner label="Creating..." /> : 'Register'}</button>
      </form>
      <p className="mt-4 text-sm">Already registered? <Link className="font-semibold text-brand-600" to="/login">Log in</Link></p>
    </Shell>
  )
}
