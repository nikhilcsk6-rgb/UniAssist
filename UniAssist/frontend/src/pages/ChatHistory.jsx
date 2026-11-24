import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import toast from 'react-hot-toast'
import { api } from '../api/client'
import { Badge, Card, Empty, PageHeader } from '../components/ui'

export default function ChatHistory() {
  const [q, setQ] = useState('')
  const [items, setItems] = useState([])
  const load = () => api(`/chat/sessions${q ? `?q=${encodeURIComponent(q)}` : ''}`).then((d) => setItems(d.sessions)).catch((e) => toast.error(e.message))
  useEffect(() => { const t = setTimeout(load, 300); return () => clearTimeout(t) }, [q])

  async function rename(s) {
    const title = window.prompt('New title', s.title)
    if (title) try { await api(`/chat/sessions/${s.id}`, { method: 'PUT', body: { title } }); load() } catch (e) { toast.error(e.message) }
  }
  async function remove(s) {
    if (window.confirm('Delete this conversation?')) try { await api(`/chat/sessions/${s.id}`, { method: 'DELETE' }); load(); toast.success('Deleted') } catch (e) { toast.error(e.message) }
  }
  return (
    <>
      <PageHeader title="Chat History" subtitle="Your conversations are private to you." />
      <label htmlFor="hq" className="sr-only">Search conversations</label>
      <input id="hq" className="input mb-4 max-w-md" placeholder="Search titles and messages…" value={q} onChange={(e) => setQ(e.target.value)} />
      {items.length === 0 ? <Empty>No conversations found.</Empty> : (
        <div className="space-y-2">
          {items.map((s) => (
            <Card key={s.id} className="flex flex-wrap items-center justify-between gap-2 !p-4">
              <Link to={`/app/chat/${s.id}`} className="min-w-0 flex-1">
                <p className="truncate font-medium text-navy-900 hover:text-brand-600 dark:text-white">{s.title}</p>
                <p className="text-xs text-slate-500">{s.created_at.slice(0, 16).replace('T', ' ')} · <Badge>{s.mode}</Badge></p>
              </Link>
              <div className="flex gap-2"><button className="btn btn-ghost !py-1 text-xs" onClick={() => rename(s)}>Rename</button><button className="btn btn-ghost !py-1 text-xs" onClick={() => remove(s)}>Delete</button></div>
            </Card>
          ))}
        </div>
      )}
    </>
  )
}
