import { useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import { api } from '../api/client'
import { useAuth } from '../context/AuthContext'
import FileDrop from '../components/FileDrop'
import { Badge, Card, Empty, Field, PageHeader, Spinner } from '../components/ui'

export default function KnowledgeBase() {
  const { user } = useAuth()
  const isAdmin = user.role === 'admin'
  const [docs, setDocs] = useState([])
  const [file, setFile] = useState(null)
  const [f, setF] = useState({ title: '', category: isAdmin ? 'official' : 'study_material', visibility: 'public' })
  const [busy, setBusy] = useState(false)
  const load = () => api('/documents').then((d) => setDocs(d.documents)).catch((e) => toast.error(e.message))
  useEffect(() => { load() }, [])

  async function upload() {
    if (!file) return toast.error('Choose a file first.')
    setBusy(true)
    const form = new FormData()
    form.append('file', file); form.append('title', f.title); form.append('category', f.category); form.append('visibility', f.visibility)
    try { await api('/documents', { method: 'POST', form }); toast.success('Uploaded and indexed'); setFile(null); setF({ ...f, title: '' }); load() }
    catch (e) { toast.error(e.message); load() } finally { setBusy(false) }
  }
  async function reindex(d) { try { await api(`/documents/${d.id}/reindex`, { method: 'POST' }); toast.success('Re-indexed'); load() } catch (e) { toast.error(e.message) } }
  async function remove(d) {
    if (window.confirm(`Delete "${d.title}" and remove it from the knowledge base?`)) try { await api(`/documents/${d.id}`, { method: 'DELETE' }); load() } catch (e) { toast.error(e.message) }
  }
  const cats = isAdmin ? [['official', 'Official university document']] : [['study_material', 'Study material'], ['personal', 'Personal']]
  const canManage = (d) => isAdmin || d.owner_id === user.id
  return (
    <>
      <PageHeader title="Knowledge Base" subtitle={isAdmin ? 'Official documents feed the university chatbot.' : 'Share study material with students.'} />
      <div className="grid gap-4 lg:grid-cols-3">
        <Card title="Upload & index">
          <div className="space-y-3">
            <FileDrop file={file} onFile={setFile} />
            <Field label="Title" id="kt"><input id="kt" className="input" placeholder="Defaults to file name" value={f.title} onChange={(e) => setF({ ...f, title: e.target.value })} /></Field>
            <Field label="Category" id="kc"><select id="kc" className="input" value={f.category} onChange={(e) => setF({ ...f, category: e.target.value })}>{cats.map(([k, l]) => <option key={k} value={k}>{l}</option>)}</select></Field>
            {!isAdmin && f.category === 'study_material' && <Field label="Visibility" id="kv"><select id="kv" className="input" value={f.visibility} onChange={(e) => setF({ ...f, visibility: e.target.value })}><option value="public">Shared with all students</option><option value="private">Only me</option></select></Field>}
            <button className="btn btn-primary w-full" disabled={busy || !file} onClick={upload}>{busy ? <Spinner label="Indexing…" /> : 'Upload'}</button>
          </div>
        </Card>
        <Card title={`Documents (${docs.length})`} className="lg:col-span-2 overflow-x-auto">
          {docs.length === 0 ? <Empty>The knowledge base is empty.</Empty> : (
            <table className="w-full text-sm">
              <thead><tr className="text-left text-slate-500"><th className="pb-2">Title</th><th>Category</th><th>Status</th><th>Chunks</th><th /></tr></thead>
              <tbody>{docs.map((d) => (
                <tr key={d.id} className="border-t border-slate-100 dark:border-navy-700">
                  <td className="py-2 pr-2"><div className="font-medium">{d.title}</div><div className="text-xs text-slate-500">{d.filename} · {d.page_count} p.</div></td>
                  <td><Badge color={d.category === 'official' ? 'purple' : 'navy'}>{d.category}</Badge> <span className="text-xs text-slate-500">{d.visibility}</span></td>
                  <td><Badge color={d.status === 'indexed' ? 'green' : 'red'}>{d.status}</Badge></td>
                  <td>{d.chunk_count}</td>
                  <td className="space-x-1 whitespace-nowrap text-right">{canManage(d) && <><button className="btn btn-ghost !px-2 !py-1 text-xs" onClick={() => reindex(d)}>Re-index</button><button className="btn btn-ghost !px-2 !py-1 text-xs" onClick={() => remove(d)}>Delete</button></>}</td>
                </tr>))}</tbody>
            </table>
          )}
        </Card>
      </div>
    </>
  )
}
