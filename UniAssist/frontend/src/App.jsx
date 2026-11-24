import { Navigate, Route, Routes } from 'react-router-dom'
import { useAuth } from './context/AuthContext'
import Layout from './components/Layout'
import { Spinner } from './components/ui'
import Landing from './pages/Landing'
import { Login, Register } from './pages/AuthPages'
import Dashboard from './pages/Dashboard'
import Chatbot from './pages/Chatbot'
import DocumentAssistant from './pages/DocumentAssistant'
import QuestionGenerator from './pages/QuestionGenerator'
import StudyAssistant from './pages/StudyAssistant'
import QuizPage from './pages/QuizPage'
import Announcements from './pages/Announcements'
import ChatHistory from './pages/ChatHistory'
import KnowledgeBase from './pages/KnowledgeBase'
import Users from './pages/Users'
import Research from './pages/Research'
import Feedback from './pages/Feedback'
import { Profile, Settings } from './pages/ProfileSettings'

function Protected({ roles, children }) {
  const { user, loading } = useAuth()
  if (loading) return <div className="p-10"><Spinner /></div>
  if (!user) return <Navigate to="/login" replace />
  if (roles && !roles.includes(user.role)) return <Navigate to="/app" replace />
  return children
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/app" element={<Protected><Layout /></Protected>}>
        <Route index element={<Dashboard />} />
        <Route path="chat" element={<Chatbot />} />
        <Route path="chat/:sessionId" element={<Chatbot />} />
        <Route path="documents" element={<DocumentAssistant />} />
        <Route path="questions" element={<QuestionGenerator />} />
        <Route path="study" element={<StudyAssistant />} />
        <Route path="quiz" element={<QuizPage />} />
        <Route path="quiz/:quizId" element={<QuizPage />} />
        <Route path="announcements" element={<Announcements />} />
        <Route path="history" element={<ChatHistory />} />
        <Route path="knowledge" element={<Protected roles={['admin', 'faculty']}><KnowledgeBase /></Protected>} />
        <Route path="users" element={<Protected roles={['admin']}><Users /></Protected>} />
        <Route path="research" element={<Protected roles={['admin']}><Research /></Protected>} />
        <Route path="feedback" element={<Feedback />} />
        <Route path="profile" element={<Profile />} />
        <Route path="settings" element={<Settings />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
