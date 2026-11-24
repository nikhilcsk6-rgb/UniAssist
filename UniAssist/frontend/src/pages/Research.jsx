import { useEffect, useState } from 'react'
import { Bar, Line } from 'react-chartjs-2'
import 'chart.js/auto'
import toast from 'react-hot-toast'
import { api, saveBlob } from '../api/client'
import { Badge, Card, Empty, Field, PageHeader, Spinner } from '../components/ui'

const A = '#94a3b8', B = '#7c3aed'
const num = (v, d = 3) => (v == null ? 'n/a' : v.toFixed(d))
const pct = (v) => (v == null ? 'n/a' : `${(v * 100).toFixed(1)}%`)

export default function Research() {
  const [datasets, setDatasets] = useState([])
  const [exps, setExps] = useState([])
  const [detail, setDetail] = useState(null)
  const [file, setFile] = useState(null)
  const [dsName, setDsName] = useState('')
  const [run, setRun] = useState({ name: '', dataset_name: '', top_k: 5, temperature: 0.1, limit: 30 })
  const [busy, setBusy] = useState(false)

  const load = () => {
    api('/research/datasets').then((d) => setDatasets(d.datasets)).catch((e) => toast.error(e.message))
    api('/research/experiments').then((d) => setExps(d.experiments)).catch(() => {})
  }
  useEffect(load, [])

  async function uploadBench() {
    if (!file || !dsName.trim()) return toast.error('Choose a CSV and enter a dataset name.')
    const form = new FormData(); form.append('file', file); form.append('dataset_name', dsName)
    try { const d = await api('/research/benchmark', { method: 'POST', form }); toast.success(`${d.rows} benchmark questions saved`); setFile(null); load() } catch (e) { toast.error(e.message) }
  }
  async function runExp() {
    if (!run.dataset_name) return toast.error('Select a dataset.')
    setBusy(true)
    try {
      const d = await api('/research/experiments', { method: 'POST', body: { ...run, top_k: Number(run.top_k), temperature: Number(run.temperature), limit: Number(run.limit) } })
      toast.success('Experiment completed'); load(); open(d.experiment.id)
    } catch (e) { toast.error(e.message); load() } finally { setBusy(false) }
  }
  const open = (id) => api(`/research/experiments/${id}`).then(setDetail).catch((e) => toast.error(e.message))
  const exp = (id, kind) => api(`/research/experiments/${id}/export.${kind}`, { blob: true }).then((b) => saveBlob(b, `experiment_${id}.${kind}`)).catch((e) => toast.error(e.message))
  const del = (id) => window.confirm('Delete this experiment?') && api(`/research/experiments/${id}`, { method: 'DELETE' }).then(() => { setDetail(null); load() })

  const s = detail?.summary, a = s?.A_no_rag, b = s?.B_rag
  const rows = detail ? detail.rows : []
  const qIds = [...new Set(rows.map((r) => r.question_id))]
  const timeOf = (v) => qIds.map((id) => rows.find((r) => r.question_id === id && r.variant === v)?.response_time_ms ?? null)

  return (
    <>
      <PageHeader title="Research Analytics" subtitle="Model A (LLM only) vs Model B (same LLM + RAG). Every figure below is computed from experiments you run; nothing is pre-filled." />
      <div className="grid gap-4 lg:grid-cols-2">
        <Card title="1. Benchmark dataset">
          <p className="mb-2 text-xs text-slate-500">CSV columns: <code>question, reference_answer, reference_document, reference_page</code> (last two optional, needed for citation and retrieval metrics).</p>
          <div className="space-y-2">
            <input aria-label="CSV file" type="file" accept=".csv" className="input" onChange={(e) => setFile(e.target.files[0])} />
            <Field label="Dataset name" id="dn"><input id="dn" className="input" value={dsName} onChange={(e) => setDsName(e.target.value)} /></Field>
            <button className="btn btn-navy" onClick={uploadBench}>Upload dataset</button>
          </div>
          {datasets.length > 0 && <ul className="mt-3 text-sm">{datasets.map((d) => <li key={d.name} className="flex justify-between border-t border-slate-100 py-1 dark:border-navy-700"><span>{d.name}</span><Badge>{d.rows} questions</Badge></li>)}</ul>}
        </Card>
        <Card title="2. Run experiment">
          <div className="grid grid-cols-2 gap-3">
            <Field label="Name" id="en"><input id="en" className="input" value={run.name} onChange={(e) => setRun({ ...run, name: e.target.value })} /></Field>
            <Field label="Dataset" id="ed"><select id="ed" className="input" value={run.dataset_name} onChange={(e) => setRun({ ...run, dataset_name: e.target.value })}><option value="">Select…</option>{datasets.map((d) => <option key={d.name}>{d.name}</option>)}</select></Field>
            <Field label="Top-k chunks" id="ek"><input id="ek" type="number" min="1" max="10" className="input" value={run.top_k} onChange={(e) => setRun({ ...run, top_k: e.target.value })} /></Field>
            <Field label="Temperature" id="et"><input id="et" type="number" step="0.1" min="0" max="1" className="input" value={run.temperature} onChange={(e) => setRun({ ...run, temperature: e.target.value })} /></Field>
            <Field label="Max questions (≤50)" id="el"><input id="el" type="number" min="1" max="50" className="input" value={run.limit} onChange={(e) => setRun({ ...run, limit: e.target.value })} /></Field>
          </div>
          <p className="mt-2 text-xs text-slate-500">Each question makes ~4 LLM calls (2 answers + 2 judgements); a run can take several minutes and uses API quota.</p>
          <button className="btn btn-primary mt-3" disabled={busy} onClick={runExp}>{busy ? <Spinner label="Running… please wait" /> : 'Run experiment'}</button>
        </Card>
      </div>

      <Card title="Past experiments" className="mt-4">
        {exps.length === 0 ? <Empty>No experiments yet. Upload a dataset and run one.</Empty> : (
          <ul className="space-y-2">{exps.map((e) => (
            <li key={e.id}><button className="btn btn-ghost w-full justify-between" onClick={() => open(e.id)}>
              <span>{e.name} · {e.dataset_name} · {e.created_at.slice(0, 16).replace('T', ' ')}</span>
              <span className="flex gap-1"><Badge color={e.is_sample ? 'amber' : 'green'}>{e.is_sample ? 'sample data' : 'measured'}</Badge><Badge color={e.status === 'completed' ? 'green' : 'red'}>{e.status}</Badge></span>
            </button></li>))}</ul>
        )}
      </Card>

      {detail && a && b && (
        <>
          <PageHeader title={`Results: ${detail.experiment.name}`} subtitle={`${detail.experiment.llm_model} · temperature ${detail.experiment.temperature} · top-k ${detail.experiment.top_k} · ${a.n} questions`}>
            <Badge color={detail.experiment.is_sample ? 'amber' : 'green'}>{detail.experiment.is_sample ? 'SAMPLE DATA' : 'MEASURED RESULTS'}</Badge>
            <button className="btn btn-ghost" onClick={() => exp(detail.experiment.id, 'csv')}>⬇ CSV</button>
            <button className="btn btn-ghost" onClick={() => exp(detail.experiment.id, 'pdf')}>⬇ PDF</button>
            <button className="btn btn-ghost" onClick={() => del(detail.experiment.id)}>Delete</button>
          </PageHeader>
          <div className="grid gap-4 lg:grid-cols-2">
            <Card title="Quality metrics (higher is better)">
              <Bar options={{ scales: { y: { min: 0, max: 1 } } }} data={{ labels: ['Accuracy', 'Relevance', 'Citation accuracy', 'Retrieval precision'], datasets: [
                { label: 'A: no RAG', data: [a.accuracy, a.relevance, null, null], backgroundColor: A },
                { label: 'B: RAG', data: [b.accuracy, b.relevance, b.citation_accuracy, b.retrieval_precision], backgroundColor: B }] }} />
            </Card>
            <Card title="Hallucination & abstention rate (lower hallucination is better)">
              <Bar options={{ scales: { y: { min: 0, max: 1 } } }} data={{ labels: ['Hallucination rate', 'Abstention rate'], datasets: [
                { label: 'A: no RAG', data: [a.hallucination_rate, a.abstention_rate], backgroundColor: A },
                { label: 'B: RAG', data: [b.hallucination_rate, b.abstention_rate], backgroundColor: B }] }} />
            </Card>
            <Card title="Response time per question (ms)" className="lg:col-span-2">
              <Line data={{ labels: qIds.map((_, i) => `Q${i + 1}`), datasets: [
                { label: 'A: no RAG', data: timeOf('A_no_rag'), borderColor: A, tension: 0.2 }, { label: 'B: RAG', data: timeOf('B_rag'), borderColor: B, tension: 0.2 }] }} />
            </Card>
          </div>
          <Card title="Comparison table" className="mt-4 overflow-x-auto">
            <table className="w-full text-sm">
              <thead><tr className="text-left text-slate-500"><th>Metric</th><th>Model A (no RAG)</th><th>Model B (RAG)</th></tr></thead>
              <tbody>
                {[['Answer accuracy (0-1)', num(a.accuracy), num(b.accuracy)], ['Response relevance (0-1)', num(a.relevance), num(b.relevance)],
                  ['Hallucination rate', pct(a.hallucination_rate), pct(b.hallucination_rate)], ['Abstention rate ("not available")', pct(a.abstention_rate), pct(b.abstention_rate)],
                  ['Avg response time', `${num(a.avg_time_ms, 0)} ms`, `${num(b.avg_time_ms, 0)} ms`], ['Citation accuracy', 'n/a', pct(b.citation_accuracy)],
                  ['Retrieval precision', 'n/a', pct(b.retrieval_precision)],
                  ['User satisfaction (avg rating /5)', 'not collected', `${num(detail.satisfaction.average_rating, 2)} (n=${detail.satisfaction.count})`]].map((r) => (
                  <tr key={r[0]} className="border-t border-slate-100 dark:border-navy-700"><td className="py-1.5">{r[0]}</td><td>{r[1]}</td><td className="font-semibold">{r[2]}</td></tr>))}
              </tbody>
            </table>
            <p className="mt-3 text-xs text-slate-500">Accuracy, relevance and hallucination are judged by the same LLM against your verified reference answers (LLM-as-judge); spot-check a sample manually before reporting. User satisfaction comes from real ratings of RAG chatbot answers only.</p>
          </Card>
          <Card title="Per-question answers" className="mt-4">
            <details><summary className="cursor-pointer text-sm font-medium">Show {qIds.length} questions</summary>
              <div className="mt-3 space-y-3">{qIds.map((id) => { const r = rows.filter((x) => x.question_id === id); return (
                <div key={id} className="rounded-xl border border-slate-200 p-3 text-sm dark:border-navy-700">
                  <p className="font-semibold">{r[0].question}</p><p className="text-xs text-slate-500">Reference: {r[0].reference_answer}</p>
                  {r.map((x) => <p key={x.variant} className="mt-1"><Badge color={x.variant === 'B_rag' ? 'purple' : 'navy'}>{x.variant}</Badge> acc {num(x.accuracy, 1)}{x.hallucinated ? ' · hallucinated' : ''}{x.abstained ? ' · abstained' : ''} - {x.answer?.slice(0, 200)}</p>)}
                </div>) })}</div>
            </details>
          </Card>
        </>
      )}
    </>
  )
}
