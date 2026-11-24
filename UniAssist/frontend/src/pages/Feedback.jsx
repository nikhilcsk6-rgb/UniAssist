import { useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import { api } from '../api/client'
import { useAuth } from '../context/AuthContext'
import { Badge, Card, Empty, Field, PageHeader } from '../components/ui'

export default function Feedback() {
  const { user } = useAuth()
  const [text, setText] = useState('')
  const [list, setList] = useState([])
  const [type, setType] = useState('')
  const isAdmin = user.role === 'admin'
  const load = () => api(isAdmin ? `/feedback${type ? `?type=${type}` : ''}` : '/feedback/mine').then((d) => setList(d.feedback)).catch((e) => toast.error(e.message))
  useEffect(() => { load() }, [type])

  async function submit(e) {
    e.preventDefault()
    try { await api('/feedback', { method: 'POST', body: { type: 'suggestion', comment: text } }); toast.success('Thank you for your suggestion!'); setText(''); load() }
    catch (err) { toast.error(err.message) }
  }
  const color = { rating: 'green', incorrect_report: 'red', suggestion: 'purple' }
  return (
    <>
      <PageHeader title="Feedback" subtitle="Rate answers inside the chatbot (👍 👎 🚩) or send a suggestion here." />
      <div className="grid gap-4 lg:grid-cols-3">
        <Card title="Send a suggestion">
          <form onSubmit={submit} className="space-y-3">
            <Field label="Your suggestion" id="fs"><textarea id="fs" required rows="5" maxLength={2000} className="input" value={text} onChange={(e) => setText(e.target.value)} /></Field>
            <button className="btn btn-primary w-full">Submit</button>
          </form>
        </Card>
        <Card title={isAdmin ? 'All feedback' : 'My feedback'} className="lg:col-span-2">
          {isAdmin && <div className="mb-3 flex flex-wrap gap-2">{['', 'rating', 'incorrect_report', 'suggestion'].map((t) => <button key={t || 'all'} className={`btn ${type === t ? 'btn-primary' : 'btn-ghost'}`} onClick={() => setType(t)}>{t || 'All'}</button>)}</div>}
          {list.length === 0 ? <Empty>Nothing here yet.</Empty> : (
            <ul className="space-y-2">{list.map((f) => (
              <li key={f.id} className="rounded-xl border border-slate-200 p-3 text-sm dark:border-navy-700">
                <div className="flex items-center gap-2"><Badge color={color[f.type]}>{f.type.replace('_', ' ')}</Badge>{f.rating && <span>{'★'.repeat(f.rating)}</span>}{isAdmin && <span className="text-xs text-slate-500">{f.user}</span>}<span className="ml-auto text-xs text-slate-500">{f.created_at.slice(0, 10)}</span></div>
                {f.comment && <p className="mt-1">{f.comment}</p>}
              </li>))}</ul>
          )}
        </Card>
      </div>
    </>
  )
}
