import { useEffect, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import toast from 'react-hot-toast'
import { api } from '../api/client'
import { useAuth } from '../context/AuthContext'
import { Badge, LangSelect, Md, PageHeader, Spinner } from '../components/ui'

const SUGGESTIONS = ['What is the MCA tuition fee?', 'What attendance is required for exams?', 'What scholarships are available?', 'What are the library timings?']
const MODES = { university: 'University documents', document: 'A specific document', study: 'All my accessible documents' }

function Message({ m, onRate, onReport }) {
  const mine = m.sender === 'user'
  return (
    <div className={`flex ${mine ? 'justify-end' : 'justify-start'} animate-fadeUp`}>
      <div className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm ${mine ? 'bg-brand-600 text-white' : m.grounded === false ? 'border border-amber-300 bg-amber-50 text-amber-900 dark:border-amber-700 dark:bg-amber-950 dark:text-amber-100' : 'border border-slate-200 bg-white dark:border-navy-700 dark:bg-navy-900'}`}>
        {mine ? <p className="whitespace-pre-wrap">{m.content}</p> : <Md>{m.content}</Md>}
        {!mine && m.sources?.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-1.5" aria-label="Sources">
            {m.sources.map((s) => (
              <span key={s.n} title={s.snippet} className="badge bg-navy-100 text-navy-800 dark:bg-navy-700 dark:text-navy-100">[{s.n}] {s.filename} · p.{s.page}</span>
            ))}
          </div>
        )}
        {!mine && m.id && (
          <div className="mt-2 flex items-center gap-2 text-xs text-slate-500">
            <button className="hover:text-emerald-600" aria-label="Helpful answer" onClick={() => onRate(m, 5)}>👍</button>
            <button className="hover:text-red-600" aria-label="Not helpful" onClick={() => onRate(m, 1)}>👎</button>
            <button className="hover:text-amber-600" onClick={() => onReport(m)}>🚩 Report incorrect</button>
            {m.response_time_ms != null && <span>{(m.response_time_ms / 1000).toFixed(1)}s</span>}
            {m.grounded === false && <Badge color="amber">Not in documents</Badge>}
          </div>
        )}
      </div>
    </div>
  )
}

export default function Chatbot() {
  const { sessionId } = useParams()
  const nav = useNavigate()
  const { user } = useAuth()
  const [session, setSession] = useState(null)
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [busy, setBusy] = useState(false)
  const [mode, setMode] = useState('university')
  const [lang, setLang] = useState(user.preferred_language)
  const [docs, setDocs] = useState([])
  const [docId, setDocId] = useState('')
  const bottom = useRef(null)

  useEffect(() => { api('/documents').then((d) => setDocs(d.documents)).catch(() => {}) }, [])
  useEffect(() => {
    if (!sessionId) { setSession(null); setMessages([]); return }
    if (session && String(session.id) === String(sessionId)) return
    api(`/chat/sessions/${sessionId}`).then((d) => { setSession(d.session); setMessages(d.messages); setMode(d.session.mode); setLang(d.session.language) })
      .catch((e) => { toast.error(e.message); nav('/app/chat') })
  }, [sessionId])
  useEffect(() => { bottom.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages, busy])

  async function send(text) {
    const content = (text ?? input).trim()
    if (!content || busy) return
    if (!session && mode === 'document' && !docId) return toast.error('Choose a document first.')
    setBusy(true); setInput('')
    try {
      let s = session
      if (!s) {
        s = (await api('/chat/sessions', { method: 'POST', body: { mode, language: lang, document_id: mode === 'document' ? Number(docId) : undefined } })).session
        setSession(s); nav(`/app/chat/${s.id}`, { replace: true })
      }
      setMessages((m) => [...m, { sender: 'user', content }])
      const d = await api(`/chat/sessions/${s.id}/messages`, { method: 'POST', body: { content } })
      setMessages((m) => [...m.slice(0, -1), d.user_message, d.assistant_message])
    } catch (e) { toast.error(e.message); setMessages((m) => m.filter((x) => x.id)) }
    finally { setBusy(false) }
  }

  const rate = (m, rating) => api('/feedback', { method: 'POST', body: { type: 'rating', message_id: m.id, rating } }).then(() => toast.success('Thanks for your feedback')).catch((e) => toast.error(e.message))
  const report = (m) => {
    const comment = window.prompt('What was wrong with this answer?')
    if (comment) api('/feedback', { method: 'POST', body: { type: 'incorrect_report', message_id: m.id, comment } }).then(() => toast.success('Report submitted')).catch((e) => toast.error(e.message))
  }
  async function changeLang(v) {
    setLang(v)
    if (session) api(`/chat/sessions/${session.id}`, { method: 'PUT', body: { language: v } }).catch(() => {})
  }

  return (
    <div className="mx-auto flex h-[calc(100vh-8rem)] max-w-4xl flex-col">
      <PageHeader title="AI University Chatbot" subtitle="Answers come only from documents, with sources. Unknown answers are reported honestly.">
        <button className="btn btn-ghost" onClick={() => nav('/app/chat')}>＋ New chat</button>
      </PageHeader>
      <div className="mb-3 flex flex-wrap items-center gap-2">
        <label className="sr-only" htmlFor="mode">Knowledge source</label>
        <select id="mode" className="input w-auto" value={mode} disabled={!!session} onChange={(e) => setMode(e.target.value)}>
          {Object.entries(MODES).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
        </select>
        {mode === 'document' && !session && (
          <select aria-label="Document" className="input w-auto max-w-xs" value={docId} onChange={(e) => setDocId(e.target.value)}>
            <option value="">Select a document…</option>
            {docs.map((d) => <option key={d.id} value={d.id}>{d.title}</option>)}
          </select>
        )}
        <LangSelect value={lang} onChange={changeLang} />
      </div>
      <div className="flex-1 space-y-3 overflow-y-auto rounded-2xl border border-slate-200 bg-slate-100/60 p-4 dark:border-navy-700 dark:bg-navy-950" aria-live="polite">
        {messages.length === 0 && (
          <div className="mt-10 text-center">
            <div className="text-5xl" aria-hidden="true">🎓</div>
            <p className="mt-2 font-semibold text-navy-900 dark:text-white">How can I help you today?</p>
            <div className="mt-4 flex flex-wrap justify-center gap-2">{SUGGESTIONS.map((s) => <button key={s} className="btn btn-ghost text-xs" onClick={() => send(s)}>{s}</button>)}</div>
          </div>
        )}
        {messages.map((m, i) => <Message key={m.id ? `m${m.id}` : `tmp${i}`} m={m} onRate={rate} onReport={report} />)}
        {busy && <div className="pl-2"><Spinner label="Searching documents and thinking..." /></div>}
        <div ref={bottom} />
      </div>
      <form className="mt-3 flex gap-2" onSubmit={(e) => { e.preventDefault(); send() }}>
        <label htmlFor="chat-input" className="sr-only">Your question</label>
        <input id="chat-input" className="input" placeholder="Ask a question…" maxLength={2000} value={input} onChange={(e) => setInput(e.target.value)} />
        <button className="btn btn-primary" disabled={busy || !input.trim()}>Send</button>
      </form>
    </div>
  )
}
