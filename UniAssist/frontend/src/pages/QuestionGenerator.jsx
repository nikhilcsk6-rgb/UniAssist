import { useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import { api, saveBlob } from '../api/client'
import { useAuth } from '../context/AuthContext'
import { Badge, Card, Empty, Field, LangSelect, PageHeader, Spinner } from '../components/ui'

const TYPES = [['mcq', 'Multiple choice'], ['short', 'Short answer'], ['long', 'Long answer'], ['true_false', 'True / False']]
const DIFFS = ['easy', 'medium', 'difficult']
const PRESETS = {
  'Internal test (20 marks)': [{ type: 'mcq', marks: 1, difficulty: 'easy', count: 5 }, { type: 'short', marks: 5, difficulty: 'medium', count: 3 }],
  'End-semester style': [{ type: 'mcq', marks: 1, difficulty: 'easy', count: 10 }, { type: 'short', marks: 2, difficulty: 'medium', count: 5 }, { type: 'short', marks: 5, difficulty: 'medium', count: 4 }, { type: 'long', marks: 10, difficulty: 'difficult', count: 3 }],
  'True/False drill': [{ type: 'true_false', marks: 1, difficulty: 'easy', count: 10 }],
}

export default function QuestionGenerator() {
  const { user } = useAuth()
  const [docs, setDocs] = useState([])
  const [docId, setDocId] = useState('')
  const [topic, setTopic] = useState('')
  const [title, setTitle] = useState('Question Paper')
  const [lang, setLang] = useState(user.preferred_language)
  const [spec, setSpec] = useState(PRESETS['Internal test (20 marks)'])
  const [paper, setPaper] = useState(null)
  const [papers, setPapers] = useState([])
  const [showAns, setShowAns] = useState(false)
  const [busy, setBusy] = useState(false)

  const loadPapers = () => api('/questions/papers').then((d) => setPapers(d.papers)).catch(() => {})
  useEffect(() => { api('/documents').then((d) => setDocs(d.documents)).catch(() => {}); loadPapers() }, [])
  const setRow = (i, k, v) => setSpec(spec.map((r, j) => (j === i ? { ...r, [k]: v } : r)))

  async function generate() {
    if (!docId && !topic.trim()) return toast.error('Choose a document or enter a topic.')
    setBusy(true); setPaper(null)
    try {
      const body = { title, language: lang, spec: spec.map((r) => ({ ...r, count: Number(r.count), marks: Number(r.marks) })), document_id: docId ? Number(docId) : undefined, topic: docId ? undefined : topic }
      setPaper(await api('/questions/generate', { method: 'POST', body })); loadPapers(); toast.success('Question paper generated')
    } catch (e) { toast.error(e.message) } finally { setBusy(false) }
  }
  async function openPaper(id) { try { setPaper(await api(`/questions/papers/${id}`)) } catch (e) { toast.error(e.message) } }
  async function pdf(answers) {
    try { saveBlob(await api(`/questions/papers/${paper.paper_id}/pdf?answers=${answers ? 1 : 0}`, { blob: true }), `${paper.title || 'paper'}${answers ? '_answers' : ''}.pdf`) } catch (e) { toast.error(e.message) }
  }
  const total = paper?.questions.reduce((a, q) => a + (q.marks || 0), 0)

  return (
    <>
      <PageHeader title="Question Paper Generator" subtitle="Create exam questions with answer keys from study material and export to PDF." />
      <div className="grid gap-4 lg:grid-cols-3">
        <Card title="Paper setup" className="lg:col-span-2">
          <div className="grid gap-3 sm:grid-cols-2">
            <Field label="Title" id="qt"><input id="qt" className="input" value={title} onChange={(e) => setTitle(e.target.value)} /></Field>
            <Field label="Language" id="ql"><LangSelect id="ql" value={lang} onChange={setLang} /></Field>
            <Field label="Source document" id="qd"><select id="qd" className="input" value={docId} onChange={(e) => setDocId(e.target.value)}><option value="">None (use a topic)</option>{docs.map((d) => <option key={d.id} value={d.id}>{d.title}</option>)}</select></Field>
            {!docId && <Field label="Topic" id="qtopic"><input id="qtopic" className="input" placeholder="e.g. Database normalization" value={topic} onChange={(e) => setTopic(e.target.value)} /></Field>}
          </div>
          <div className="mt-4 flex flex-wrap gap-2">{Object.keys(PRESETS).map((p) => <button key={p} className="btn btn-ghost text-xs" onClick={() => setSpec(PRESETS[p])}>{p}</button>)}</div>
          <div className="mt-3 space-y-2">
            {spec.map((r, i) => (
              <div key={i} className="grid grid-cols-2 gap-2 sm:grid-cols-5">
                <select aria-label="Question type" className="input" value={r.type} onChange={(e) => setRow(i, 'type', e.target.value)}>{TYPES.map(([k, l]) => <option key={k} value={k}>{l}</option>)}</select>
                <select aria-label="Marks" className="input" value={r.marks} onChange={(e) => setRow(i, 'marks', e.target.value)}>{[1, 2, 5, 10].map((m) => <option key={m} value={m}>{m} mark{m > 1 ? 's' : ''}</option>)}</select>
                <select aria-label="Difficulty" className="input" value={r.difficulty} onChange={(e) => setRow(i, 'difficulty', e.target.value)}>{DIFFS.map((d) => <option key={d}>{d}</option>)}</select>
                <input aria-label="Count" type="number" min="1" max="20" className="input" value={r.count} onChange={(e) => setRow(i, 'count', e.target.value)} />
                <button className="btn btn-ghost" onClick={() => setSpec(spec.filter((_, j) => j !== i))} aria-label="Remove row">✕</button>
              </div>
            ))}
            <button className="btn btn-ghost" onClick={() => setSpec([...spec, { type: 'mcq', marks: 1, difficulty: 'easy', count: 5 }])}>＋ Add row</button>
          </div>
          <button className="btn btn-primary mt-4" disabled={busy || spec.length === 0} onClick={generate}>{busy ? <Spinner label="Generating…" /> : 'Generate paper'}</button>
        </Card>
        <Card title="My saved papers">
          {papers.length === 0 ? <Empty>No papers yet.</Empty> : <ul className="space-y-2">{papers.map((p) => <li key={p.paper_id}><button className="btn btn-ghost w-full justify-between" onClick={() => openPaper(p.paper_id)}><span className="truncate">{p.title}</span><Badge>{p.count} Q</Badge></button></li>)}</ul>}
        </Card>
      </div>
      {paper && (
        <Card title={`${paper.title} - ${paper.questions.length} questions, ${total} marks`} className="mt-4">
          <div className="mb-3 flex flex-wrap gap-2">
            <button className="btn btn-ghost" onClick={() => setShowAns(!showAns)}>{showAns ? 'Hide' : 'Show'} answer key</button>
            <button className="btn btn-navy" onClick={() => pdf(false)}>⬇ PDF (questions)</button>
            <button className="btn btn-primary" onClick={() => pdf(true)}>⬇ PDF (with answers)</button>
          </div>
          <ol className="space-y-4">
            {paper.questions.map((q, i) => (
              <li key={i} className="rounded-xl border border-slate-200 p-3 dark:border-navy-700">
                <div className="mb-1 flex gap-2"><Badge color="navy">{q.type}</Badge><Badge>{q.marks} mark(s)</Badge><Badge color={q.difficulty === 'easy' ? 'green' : q.difficulty === 'medium' ? 'amber' : 'red'}>{q.difficulty}</Badge></div>
                <p className="font-medium">{i + 1}. {q.question}</p>
                {q.options && <ul className="mt-1 ml-4 text-sm">{q.options.map((o, j) => <li key={j}>{String.fromCharCode(65 + j)}. {o}</li>)}</ul>}
                {showAns && <p className="mt-2 rounded-lg bg-brand-50 p-2 text-sm text-brand-900 dark:bg-brand-900/30 dark:text-brand-100"><b>Answer:</b> {q.answer}</p>}
              </li>
            ))}
          </ol>
        </Card>
      )}
    </>
  )
}
