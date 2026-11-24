import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import { api } from '../api/client'
import { useAuth } from '../context/AuthContext'
import { Card, Field, LangSelect, Md, PageHeader, Spinner, Tabs } from '../components/ui'

function Flashcards({ cards }) {
  const [flipped, setFlipped] = useState({})
  return (
    <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
      {cards.map((c, i) => (
        <button key={i} onClick={() => setFlipped({ ...flipped, [i]: !flipped[i] })} aria-label={flipped[i] ? 'Show question' : 'Show answer'}
          className={`min-h-[130px] rounded-2xl border p-4 text-left text-sm transition ${flipped[i] ? 'border-brand-400 bg-brand-50 dark:bg-brand-900/30' : 'border-slate-200 bg-white dark:border-navy-700 dark:bg-navy-900'}`}>
          <span className="mb-1 block text-xs font-semibold uppercase text-brand-600">{flipped[i] ? 'Answer' : 'Question'}</span>
          {flipped[i] ? c.back : c.front}
        </button>
      ))}
    </div>
  )
}

export default function StudyAssistant() {
  const nav = useNavigate()
  const { user } = useAuth()
  const [tab, setTab] = useState('explain')
  const [docs, setDocs] = useState([])
  const [lang, setLang] = useState(user.preferred_language)
  const [f, setF] = useState({ topic: '', document_id: '', level: 'beginner', days: 7, hours: 2, goals: '', count: 10 })
  const [out, setOut] = useState(null)
  const [cards, setCards] = useState(null)
  const [busy, setBusy] = useState(false)
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value })
  useEffect(() => { api('/documents').then((d) => setDocs(d.documents)).catch(() => {}) }, [])
  const src = { document_id: f.document_id ? Number(f.document_id) : undefined, topic: f.document_id ? undefined : f.topic }

  async function go() {
    setBusy(true); setOut(null); setCards(null)
    try {
      if (tab === 'explain') setOut((await api('/assistant/explain', { method: 'POST', body: { ...src, level: f.level, language: lang } })).result)
      else if (tab === 'plan') setOut((await api('/assistant/study-plan', { method: 'POST', body: { subject: f.topic, days: Number(f.days), hours_per_day: Number(f.hours), goals: f.goals, document_id: src.document_id, language: lang } })).result)
      else if (tab === 'revision') setOut((await api('/assistant/revision-notes', { method: 'POST', body: { ...src, language: lang } })).result)
      else if (tab === 'flash') setCards((await api('/assistant/flashcards', { method: 'POST', body: { ...src, count: Number(f.count), language: lang } })).flashcards)
      else if (tab === 'practice') {
        const d = await api('/quizzes/generate', { method: 'POST', body: { ...src, count: 15, difficulty: 'difficult', language: lang, title: `Practice exam: ${f.topic || 'document'}` } })
        nav(`/app/quiz/${d.quiz.id}?timed=1`)
      }
    } catch (e) { toast.error(e.message) } finally { setBusy(false) }
  }
  const needsTopic = tab === 'plan' || !f.document_id
  const sources = (
    <>
      <Field label="Use a document (optional)" id="sd"><select id="sd" className="input" value={f.document_id} onChange={set('document_id')}><option value="">No - use a topic</option>{docs.map((d) => <option key={d.id} value={d.id}>{d.title}</option>)}</select></Field>
      {needsTopic && <Field label={tab === 'plan' ? 'Subject / exam' : 'Topic'} id="st"><input id="st" className="input" placeholder="e.g. Operating Systems - process scheduling" value={f.topic} onChange={set('topic')} /></Field>}
    </>
  )
  return (
    <>
      <PageHeader title="Study Assistant" subtitle="Explanations, plans, flashcards, revision notes and practice exams. Topic-only answers use general knowledge, not university documents." />
      <Tabs active={tab} onChange={(t) => { setTab(t); setOut(null); setCards(null) }} tabs={[['explain', 'Explain a topic'], ['plan', 'Study plan'], ['flash', 'Flashcards'], ['revision', 'Revision notes'], ['practice', 'Practice exam']]} />
      <Card>
        <div className="grid gap-3 sm:grid-cols-2">
          {sources}
          {tab === 'explain' && <Field label="Level" id="lv"><select id="lv" className="input" value={f.level} onChange={set('level')}><option>beginner</option><option>intermediate</option><option>advanced</option></select></Field>}
          {tab === 'plan' && <>
            <Field label="Days available" id="sdays"><input id="sdays" type="number" min="1" max="90" className="input" value={f.days} onChange={set('days')} /></Field>
            <Field label="Hours per day" id="shrs"><input id="shrs" type="number" min="0.5" max="12" step="0.5" className="input" value={f.hours} onChange={set('hours')} /></Field>
            <Field label="Goals / weak areas" id="sg"><input id="sg" className="input" value={f.goals} onChange={set('goals')} /></Field></>}
          {tab === 'flash' && <Field label="Number of cards" id="sc"><input id="sc" type="number" min="3" max="30" className="input" value={f.count} onChange={set('count')} /></Field>}
          <Field label="Language" id="sl"><LangSelect id="sl" value={lang} onChange={setLang} /></Field>
        </div>
        <button className="btn btn-primary mt-4" disabled={busy || (needsTopic && !f.topic.trim())} onClick={go}>{busy ? <Spinner label="Working…" /> : tab === 'practice' ? 'Start practice exam (timed quiz)' : 'Generate'}</button>
      </Card>
      {out && <Card className="mt-4"><Md>{out}</Md></Card>}
      {cards && <Flashcards cards={cards} />}
    </>
  )
}
