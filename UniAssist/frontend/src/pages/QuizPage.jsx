import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams, useSearchParams } from 'react-router-dom'
import toast from 'react-hot-toast'
import { api } from '../api/client'
import { useAuth } from '../context/AuthContext'
import { Badge, Card, Empty, Field, PageHeader, Spinner } from '../components/ui'

function Take({ id, timed }) {
  const nav = useNavigate()
  const [quiz, setQuiz] = useState(null)
  const [ans, setAns] = useState([])
  const [res, setRes] = useState(null)
  const [left, setLeft] = useState(null)
  useEffect(() => {
    api(`/quizzes/${id}`).then((d) => { setQuiz(d.quiz); setAns(Array(d.quiz.count).fill(null)); if (timed) setLeft(d.quiz.count * 60) })
      .catch((e) => { toast.error(e.message); nav('/app/quiz') })
  }, [id])
  useEffect(() => {
    if (left == null || res) return
    if (left <= 0) { submit(); return }
    const t = setTimeout(() => setLeft(left - 1), 1000)
    return () => clearTimeout(t)
  }, [left, res])
  async function submit() {
    try { setRes(await api(`/quizzes/${id}/submit`, { method: 'POST', body: { answers: ans } })) } catch (e) { toast.error(e.message) }
  }
  if (!quiz) return <Spinner />
  const mm = left != null ? `${Math.floor(left / 60)}:${String(left % 60).padStart(2, '0')}` : null
  return (
    <>
      <PageHeader title={quiz.title} subtitle={`${quiz.count} questions · ${quiz.difficulty}`}>
        {mm && !res && <Badge color={left < 60 ? 'red' : 'purple'}>⏱ {mm}</Badge>}
        <Link to="/app/quiz" className="btn btn-ghost">All quizzes</Link>
      </PageHeader>
      {res && <Card className="mb-4"><p className="text-xl font-bold">Score: {res.score} / {res.total} ({Math.round((res.score / res.total) * 100)}%)</p></Card>}
      <ol className="space-y-4">
        {quiz.questions.map((q, i) => {
          const d = res?.details[i]
          return (
            <li key={i}><Card>
              <p className="mb-2 font-medium">{i + 1}. {q.question}</p>
              <div role="radiogroup" aria-label={`Question ${i + 1}`} className="space-y-1">
                {q.options.map((o, j) => {
                  const right = d && j === d.answer_index, wrong = d && j === ans[i] && !d.correct
                  return (
                    <label key={j} className={`flex cursor-pointer items-center gap-2 rounded-lg border p-2 text-sm ${right ? 'border-emerald-500 bg-emerald-50 dark:bg-emerald-900/30' : wrong ? 'border-red-500 bg-red-50 dark:bg-red-900/30' : 'border-slate-200 dark:border-navy-700'}`}>
                      <input type="radio" name={`q${i}`} disabled={!!res} checked={ans[i] === j} onChange={() => setAns(ans.map((a, k) => (k === i ? j : a)))} />{o}
                    </label>)
                })}
              </div>
              {d?.explanation && <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">💡 {d.explanation}</p>}
            </Card></li>)
        })}
      </ol>
      {!res && <button className="btn btn-primary mt-4" onClick={submit}>Submit answers</button>}
    </>
  )
}

export default function QuizPage() {
  const { quizId } = useParams()
  const [sp] = useSearchParams()
  const nav = useNavigate()
  const { user } = useAuth()
  const [quizzes, setQuizzes] = useState([])
  const [results, setResults] = useState([])
  const [docs, setDocs] = useState([])
  const [f, setF] = useState({ topic: '', document_id: '', count: 10, difficulty: 'medium' })
  const [busy, setBusy] = useState(false)
  const load = () => { api('/quizzes').then((d) => setQuizzes(d.quizzes)).catch(() => {}); api('/quizzes/results').then((d) => setResults(d.results)).catch(() => {}) }
  useEffect(() => { if (!quizId) { load(); api('/documents').then((d) => setDocs(d.documents)).catch(() => {}) } }, [quizId])
  if (quizId) return <Take key={quizId} id={quizId} timed={sp.get('timed') === '1'} />

  async function create() {
    if (!f.document_id && !f.topic.trim()) return toast.error('Choose a document or enter a topic.')
    setBusy(true)
    try {
      const d = await api('/quizzes/generate', { method: 'POST', body: { topic: f.document_id ? undefined : f.topic, document_id: f.document_id ? Number(f.document_id) : undefined, count: Number(f.count), difficulty: f.difficulty, language: user.preferred_language } })
      nav(`/app/quiz/${d.quiz.id}`)
    } catch (e) { toast.error(e.message) } finally { setBusy(false) }
  }
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value })
  return (
    <>
      <PageHeader title="Interactive Quizzes" subtitle="Generate a quiz, answer it and get instant scoring with explanations." />
      <div className="grid gap-4 lg:grid-cols-2">
        <Card title="Create a quiz">
          <div className="space-y-3">
            <Field label="Document (optional)" id="qd"><select id="qd" className="input" value={f.document_id} onChange={set('document_id')}><option value="">None - use topic</option>{docs.map((d) => <option key={d.id} value={d.id}>{d.title}</option>)}</select></Field>
            {!f.document_id && <Field label="Topic" id="qtp"><input id="qtp" className="input" value={f.topic} onChange={set('topic')} /></Field>}
            <div className="grid grid-cols-2 gap-3">
              <Field label="Questions" id="qc"><input id="qc" type="number" min="3" max="30" className="input" value={f.count} onChange={set('count')} /></Field>
              <Field label="Difficulty" id="qdf"><select id="qdf" className="input" value={f.difficulty} onChange={set('difficulty')}><option>easy</option><option>medium</option><option>difficult</option></select></Field>
            </div>
            <button className="btn btn-primary" disabled={busy} onClick={create}>{busy ? <Spinner label="Generating…" /> : 'Generate quiz'}</button>
          </div>
        </Card>
        <Card title="Available quizzes">
          {quizzes.length === 0 ? <Empty>No quizzes yet.</Empty> : <ul className="space-y-2">{quizzes.map((q) => <li key={q.id}><Link to={`/app/quiz/${q.id}`} className="btn btn-ghost w-full justify-between"><span className="truncate">{q.title}</span><Badge>{q.count} Q</Badge></Link></li>)}</ul>}
        </Card>
      </div>
      <Card title="My results" className="mt-4">
        {results.length === 0 ? <Empty>No attempts yet.</Empty> : (
          <table className="w-full text-sm"><thead><tr className="text-left text-slate-500"><th>Quiz</th><th>Score</th><th>Date</th></tr></thead>
            <tbody>{results.map((r) => <tr key={r.id} className="border-t border-slate-100 dark:border-navy-700"><td className="py-1.5">{r.quiz_title}</td><td>{r.score}/{r.total}</td><td>{r.taken_at.slice(0, 10)}</td></tr>)}</tbody></table>
        )}
      </Card>
    </>
  )
}
