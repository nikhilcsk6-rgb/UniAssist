import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import { api } from '../api/client'
import { useAuth } from '../context/AuthContext'
import FileDrop from '../components/FileDrop'
import { Badge, Card, Empty, Field, LangSelect, Md, PageHeader, Spinner } from '../components/ui'

const TASKS = [['summary', 'Summarize'], ['key_points', 'Key points'], ['topics', 'Topic-by-topic'], ['notes', 'Study notes']]

export default function DocumentAssistant() {
  const nav = useNavigate()
  const { user } = useAuth()
  const [docs, setDocs] = useState([])
  const [file, setFile] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [sel, setSel] = useState('')
  const [lang, setLang] = useState(user.preferred_language)
  const [out, setOut] = useState(null)
  const [busy, setBusy] = useState('')

  const load = () => api('/documents').then((d) => setDocs(d.documents)).catch((e) => toast.error(e.message))
  useEffect(() => { load() }, [])

  async function upload() {
    if (!file) return
    setUploading(true)
    const form = new FormData()
    form.append('file', file); form.append('category', 'personal'); form.append('visibility', 'private')
    try { const d = await api('/documents', { method: 'POST', form }); toast.success('Document uploaded and indexed'); setFile(null); await load(); setSel(String(d.document.id)) }
    catch (e) { toast.error(e.message) } finally { setUploading(false) }
  }
  async function run(task) {
    if (!sel) return toast.error('Select a document first.')
    setBusy(task); setOut(null)
    try { setOut({ task, ...(await api(`/assistant/document/${sel}/${task}`, { method: 'POST', body: { language: lang } })) }) }
    catch (e) { toast.error(e.message) } finally { setBusy('') }
  }
  async function chat() {
    if (!sel) return toast.error('Select a document first.')
    try { const d = await api('/chat/sessions', { method: 'POST', body: { mode: 'document', document_id: Number(sel), language: lang } }); nav(`/app/chat/${d.session.id}`) }
    catch (e) { toast.error(e.message) }
  }
  async function remove() {
    if (!sel || !window.confirm('Delete this document and its index?')) return
    try { await api(`/documents/${sel}`, { method: 'DELETE' }); setSel(''); setOut(null); load(); toast.success('Deleted') } catch (e) { toast.error(e.message) }
  }
  const mine = docs.filter((d) => d.owner_id === user.id)
  const current = docs.find((d) => String(d.id) === sel)

  return (
    <>
      <PageHeader title="Document Assistant" subtitle="Upload a PDF, DOCX or TXT file (private to you) and analyse it with AI." />
      <div className="grid gap-4 lg:grid-cols-3">
        <Card title="1. Upload">
          <FileDrop file={file} onFile={setFile} />
          <button className="btn btn-primary mt-3 w-full" disabled={!file || uploading} onClick={upload}>{uploading ? <Spinner label="Indexing…" /> : 'Upload & index'}</button>
        </Card>
        <Card title="2. Choose a document" className="lg:col-span-2">
          {docs.length === 0 ? <Empty>No documents yet. Upload one to begin.</Empty> : (
            <div className="space-y-3">
              <Field label="Document" id="docsel">
                <select id="docsel" className="input" value={sel} onChange={(e) => { setSel(e.target.value); setOut(null) }}>
                  <option value="">Select…</option>
                  {mine.length > 0 && <optgroup label="My documents">{mine.map((d) => <option key={d.id} value={d.id}>{d.title}</option>)}</optgroup>}
                  <optgroup label="Shared by university / faculty">{docs.filter((d) => d.owner_id !== user.id).map((d) => <option key={d.id} value={d.id}>{d.title}</option>)}</optgroup>
                </select>
              </Field>
              {current && <p className="text-xs text-slate-500"><Badge color={current.status === 'indexed' ? 'green' : 'red'}>{current.status}</Badge> {current.page_count} page(s) · {current.chunk_count} chunks · {current.category}</p>}
              <div className="flex flex-wrap items-center gap-2">
                <LangSelect value={lang} onChange={setLang} />
                {TASKS.map(([k, l]) => <button key={k} className="btn btn-navy" disabled={!!busy} onClick={() => run(k)}>{busy === k ? <Spinner label="" /> : l}</button>)}
                <button className="btn btn-primary" onClick={chat}>💬 Chat with document</button>
                {current?.owner_id === user.id && <button className="btn btn-ghost" onClick={remove}>🗑 Delete</button>}
              </div>
            </div>
          )}
        </Card>
      </div>
      {busy && <div className="mt-4"><Spinner label="Generating…" /></div>}
      {out && (
        <Card title={`${TASKS.find((t) => t[0] === out.task)[1]} - ${out.document}`} className="mt-4">
          {out.truncated && <p className="mb-2 rounded-lg bg-amber-50 p-2 text-xs text-amber-800 dark:bg-amber-950 dark:text-amber-200">Only the first part of this long document was analysed.</p>}
          <Md>{out.result}</Md>
          <button className="btn btn-ghost mt-3" onClick={() => { navigator.clipboard.writeText(out.result); toast.success('Copied') }}>Copy</button>
        </Card>
      )}
    </>
  )
}
