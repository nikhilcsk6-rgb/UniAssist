import { useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import { api } from '../api/client'
import { useAuth } from '../context/AuthContext'
import { Badge, Card, Empty, Field, PageHeader } from '../components/ui'

const CATS = ['exam', 'event', 'holiday', 'deadline', 'circular', 'general']
const COLOR = { exam: 'red', event: 'purple', holiday: 'green', deadline: 'amber', circular: 'navy', general: 'navy' }

export default function Announcements() {
  const { user } = useAuth()
  const [items, setItems] = useState([])
  const [cat, setCat] = useState('')
  const [f, setF] = useState({ title: '', body: '', category: 'general', audience: 'all', event_date: '' })
  const canPost = user.role !== 'student'
  const load = () => api(`/announcements${cat ? `?category=${cat}` : ''}`).then((d) => setItems(d.announcements)).catch((e) => toast.error(e.message))
  useEffect(() => { load() }, [cat])
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value })

  async function post(e) {
    e.preventDefault()
    try { await api('/announcements', { method: 'POST', body: f }); toast.success('Announcement published'); setF({ ...f, title: '', body: '', event_date: '' }); load() }
    catch (err) { toast.error(err.message) }
  }
  async function remove(id) {
    if (!window.confirm('Delete this announcement?')) return
    try { await api(`/announcements/${id}`, { method: 'DELETE' }); load() } catch (e) { toast.error(e.message) }
  }
  return (
    <>
      <PageHeader title="University Announcements" subtitle="Exams, events, holidays, deadlines and circulars." />
      <div className="mb-4 flex flex-wrap gap-2">
        {['', ...CATS].map((c) => <button key={c || 'all'} className={`btn ${cat === c ? 'btn-primary' : 'btn-ghost'} capitalize`} onClick={() => setCat(c)}>{c || 'All'}</button>)}
      </div>
      <div className="grid gap-4 lg:grid-cols-3">
        <div className={`space-y-3 ${canPost ? 'lg:col-span-2' : 'lg:col-span-3'}`}>
          {items.length === 0 ? <Empty>No announcements in this category.</Empty> : items.map((a) => (
            <Card key={a.id}>
              <div className="flex items-start justify-between gap-2">
                <div><h2 className="font-semibold text-navy-900 dark:text-white">{a.title}</h2>
                  <p className="text-xs text-slate-500">By {a.author} · {a.created_at.slice(0, 10)}{a.event_date && ` · Date: ${a.event_date}`}</p></div>
                <div className="flex gap-1"><Badge color={COLOR[a.category]}>{a.category}</Badge>{a.audience !== 'all' && <Badge color="navy">{a.audience}s</Badge>}</div>
              </div>
              <p className="mt-2 whitespace-pre-wrap text-sm">{a.body}</p>
              {(user.role === 'admin' || a.author_id === user.id) && <button className="btn btn-ghost mt-2 !py-1 text-xs" onClick={() => remove(a.id)}>Delete</button>}
            </Card>
          ))}
        </div>
        {canPost && (
          <Card title="Publish announcement">
            <form onSubmit={post} className="space-y-3">
              <Field label="Title" id="at"><input id="at" required className="input" value={f.title} onChange={set('title')} /></Field>
              <Field label="Details" id="ab"><textarea id="ab" required rows="4" className="input" value={f.body} onChange={set('body')} /></Field>
              <div className="grid grid-cols-2 gap-2">
                <Field label="Category" id="ac"><select id="ac" className="input" value={f.category} onChange={set('category')}>{CATS.map((c) => <option key={c}>{c}</option>)}</select></Field>
                <Field label="Audience" id="aa"><select id="aa" className="input" value={f.audience} onChange={set('audience')}><option value="all">Everyone</option><option value="student">Students</option><option value="faculty">Faculty</option></select></Field>
              </div>
              <Field label="Event / deadline date" id="ad"><input id="ad" type="date" className="input" value={f.event_date} onChange={set('event_date')} /></Field>
              <button className="btn btn-primary w-full">Publish</button>
            </form>
          </Card>
        )}
      </div>
    </>
  )
}
