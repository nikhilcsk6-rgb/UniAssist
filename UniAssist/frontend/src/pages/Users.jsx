import { useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import { api } from '../api/client'
import { useAuth } from '../context/AuthContext'
import { Badge, Card, PageHeader, Tabs } from '../components/ui'

export default function Users() {
  const { user: me } = useAuth()
  const [tab, setTab] = useState('users')
  const [role, setRole] = useState('')
  const [users, setUsers] = useState([])
  const [logs, setLogs] = useState([])
  const loadUsers = () => api(`/admin/users${role ? `?role=${role}` : ''}`).then((d) => setUsers(d.users)).catch((e) => toast.error(e.message))
  useEffect(() => { loadUsers() }, [role])
  useEffect(() => { if (tab === 'logs') api('/admin/logs').then((d) => setLogs(d.logs)).catch((e) => toast.error(e.message)) }, [tab])

  const update = (u, body) => api(`/admin/users/${u.id}`, { method: 'PUT', body }).then(() => { toast.success('Updated'); loadUsers() }).catch((e) => toast.error(e.message))
  const remove = (u) => window.confirm(`Delete ${u.full_name}? Their documents and chats are removed too.`) && api(`/admin/users/${u.id}`, { method: 'DELETE' }).then(() => { toast.success('Deleted'); loadUsers() }).catch((e) => toast.error(e.message))

  return (
    <>
      <PageHeader title="Users & Audit Log" subtitle="Manage students and faculty; review system activity." />
      <Tabs active={tab} onChange={setTab} tabs={[['users', 'Users'], ['logs', 'Audit log']]} />
      {tab === 'users' ? (
        <Card className="overflow-x-auto">
          <div className="mb-3 flex gap-2">{['', 'student', 'faculty', 'admin'].map((r) => <button key={r || 'all'} className={`btn capitalize ${role === r ? 'btn-primary' : 'btn-ghost'}`} onClick={() => setRole(r)}>{r || 'All'}</button>)}</div>
          <table className="w-full text-sm">
            <thead><tr className="text-left text-slate-500"><th className="pb-2">Name</th><th>Email</th><th>Role</th><th>Status</th><th /></tr></thead>
            <tbody>{users.map((u) => (
              <tr key={u.id} className="border-t border-slate-100 dark:border-navy-700">
                <td className="py-2">{u.full_name}</td><td>{u.email}</td>
                <td><select aria-label={`Role of ${u.full_name}`} className="input !w-auto !py-1" value={u.role} disabled={u.id === me.id} onChange={(e) => update(u, { role: e.target.value })}><option>student</option><option>faculty</option><option>admin</option></select></td>
                <td><Badge color={u.is_active ? 'green' : 'red'}>{u.is_active ? 'active' : 'disabled'}</Badge></td>
                <td className="space-x-1 whitespace-nowrap text-right">{u.id !== me.id && <><button className="btn btn-ghost !px-2 !py-1 text-xs" onClick={() => update(u, { is_active: !u.is_active })}>{u.is_active ? 'Disable' : 'Enable'}</button><button className="btn btn-ghost !px-2 !py-1 text-xs" onClick={() => remove(u)}>Delete</button></>}</td>
              </tr>))}</tbody>
          </table>
        </Card>
      ) : (
        <Card className="overflow-x-auto"><table className="w-full text-sm"><thead><tr className="text-left text-slate-500"><th>Time (UTC)</th><th>User</th><th>Action</th><th>Details</th><th>IP</th></tr></thead>
          <tbody>{logs.map((l) => <tr key={l.id} className="border-t border-slate-100 align-top dark:border-navy-700"><td className="py-1.5 pr-2 whitespace-nowrap">{l.at.slice(0, 19).replace('T', ' ')}</td><td>{l.user_id ?? '-'}</td><td><Badge>{l.action}</Badge></td><td className="text-xs text-slate-500">{l.details ? JSON.stringify(l.details) : ''}</td><td>{l.ip}</td></tr>)}</tbody></table></Card>
      )}
    </>
  )
}
