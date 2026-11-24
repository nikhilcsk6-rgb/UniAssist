import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Bar, Doughnut, Line } from 'react-chartjs-2'
import 'chart.js/auto'
import { api } from '../api/client'
import { useAuth } from '../context/AuthContext'
import { Badge, Card, Empty, PageHeader, Spinner, StatCard } from '../components/ui'

const QUICK = [['/app/chat', '💬', 'Ask the chatbot'], ['/app/documents', '📄', 'Analyse a document'], ['/app/questions', '📝', 'Generate questions'], ['/app/study', '🎓', 'Study assistant'], ['/app/quiz', '🧠', 'Take a quiz']]
const pct = (v) => (v == null ? 'n/a' : `${(v * 100).toFixed(0)}%`)

function UserDashboard() {
  const { user } = useAuth()
  const [stats, setStats] = useState(null)
  const [ann, setAnn] = useState([])
  useEffect(() => {
    api('/analytics/me').then(setStats).catch(() => {})
    api('/announcements').then((d) => setAnn(d.announcements.slice(0, 4))).catch(() => {})
  }, [])
  const scores = stats?.recent_quiz_scores || []
  return (
    <>
      <PageHeader title={`Welcome, ${user.full_name.split(' ')[0]}`} subtitle={`${user.role === 'faculty' ? 'Faculty' : 'Student'} dashboard`} />
      {!stats ? <Spinner /> : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard icon="📄" label="My documents" value={stats.documents} />
          <StatCard icon="💬" label="Chat sessions" value={stats.chat_sessions} />
          <StatCard icon="📝" label="Papers generated" value={stats.papers_generated} />
          <StatCard icon={user.role === 'faculty' ? '📢' : '🧠'} label={user.role === 'faculty' ? 'Announcements posted' : 'Quizzes taken'} value={user.role === 'faculty' ? stats.announcements_posted : stats.quizzes_taken} />
        </div>
      )}
      <div className="mt-6 grid gap-4 lg:grid-cols-3">
        <Card title="Quick actions" className="lg:col-span-1">
          <div className="grid gap-2">{QUICK.map(([to, i, l]) => <Link key={to} to={to} className="btn btn-ghost justify-start"><span aria-hidden="true">{i}</span>{l}</Link>)}</div>
        </Card>
        <Card title="Latest announcements" className="lg:col-span-2">
          {ann.length === 0 ? <Empty>No announcements yet.</Empty> : (
            <ul className="space-y-3">{ann.map((a) => (
              <li key={a.id} className="flex items-start justify-between gap-3 border-b border-slate-100 pb-2 last:border-0 dark:border-navy-700">
                <div><p className="font-medium">{a.title}</p><p className="text-xs text-slate-500">{a.event_date || a.created_at.slice(0, 10)}</p></div>
                <Badge>{a.category}</Badge>
              </li>))}</ul>
          )}
        </Card>
      </div>
      <Card title="Recent quiz scores" className="mt-6">
        {scores.length === 0 ? <Empty>Take a quiz to see your progress here.</Empty> : (
          <Line data={{ labels: scores.map((s, i) => `#${i + 1}`), datasets: [{ label: 'Score %', data: scores.map((s) => Math.round((s.score / s.total) * 100)), borderColor: '#7c3aed', backgroundColor: '#7c3aed33', fill: true, tension: 0.3 }] }} options={{ scales: { y: { min: 0, max: 100 } } }} />
        )}
      </Card>
    </>
  )
}

function AdminDashboard() {
  const [o, setO] = useState(null)
  useEffect(() => { api('/analytics/overview').then(setO).catch(() => {}) }, [])
  if (!o) return <Spinner />
  const role = o.users_by_role
  return (
    <>
      <PageHeader title="Administrator dashboard" subtitle="System usage and AI performance (live data)" />
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard icon="👥" label="Users" value={Object.values(role).reduce((a, b) => a + b, 0)} />
        <StatCard icon="📚" label="Documents (official)" value={`${o.documents} (${o.official_documents})`} />
        <StatCard icon="💬" label="Chat sessions / messages" value={`${o.chat_sessions} / ${o.messages}`} />
        <StatCard icon="⭐" label="Average rating (1-5)" value={o.avg_rating?.toFixed(2) ?? 'n/a'} />
        <StatCard icon="🎯" label="Answers grounded in documents" value={o.rag_answers ? pct(o.grounded_answers / o.rag_answers) : 'n/a'} />
        <StatCard icon="❓" label="'Not available' rate" value={pct(o.not_found_rate)} />
        <StatCard icon="⏱️" label="Avg response time" value={o.avg_response_time_ms ? `${(o.avg_response_time_ms / 1000).toFixed(1)} s` : 'n/a'} />
        <StatCard icon="📝" label="Questions generated" value={o.questions_generated} />
      </div>
      <div className="mt-6 grid gap-4 lg:grid-cols-3">
        <Card title="Users by role"><Doughnut data={{ labels: Object.keys(role), datasets: [{ data: Object.values(role), backgroundColor: ['#0B1F4B', '#7c3aed', '#a78bfa'] }] }} /></Card>
        <Card title="Questions asked per day (14 days)" className="lg:col-span-2">
          {o.messages_per_day.length === 0 ? <Empty>No chat activity yet.</Empty> : (
            <Line data={{ labels: o.messages_per_day.map((d) => d.date), datasets: [{ label: 'Messages', data: o.messages_per_day.map((d) => d.count), borderColor: '#7c3aed', tension: 0.3 }] }} />)}
        </Card>
      </div>
      <Card title="Feedback received" className="mt-6">
        {Object.keys(o.feedback_by_type).length === 0 ? <Empty>No feedback yet.</Empty> : (
          <Bar data={{ labels: Object.keys(o.feedback_by_type), datasets: [{ label: 'Count', data: Object.values(o.feedback_by_type), backgroundColor: '#0B1F4B' }] }} />)}
      </Card>
    </>
  )
}

export default function Dashboard() {
  const { user } = useAuth()
  return user.role === 'admin' ? <AdminDashboard /> : <UserDashboard />
}
