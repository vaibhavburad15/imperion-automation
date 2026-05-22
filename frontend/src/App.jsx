import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './context/AuthContext'
import Layout from './components/Layout'
import Login from './pages/Login'
import Signup from './pages/Signup'
import Dashboard from './pages/Dashboard'
import Workflows from './pages/Workflows'
import WorkflowEditor from './pages/WorkflowEditor'
import Leads from './pages/Leads'
import Integrations from './pages/Integrations'
import Admin from './pages/Admin'

function Protected({ children }) {
  const { user } = useAuth()
  if (!user) return <Navigate to="/login" replace />
  return children
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/signup" element={<Signup />} />
      <Route path="/" element={<Protected><Layout /></Protected>}>
        <Route index element={<Dashboard />} />
        <Route path="workflows" element={<Workflows />} />
        <Route path="workflows/:id" element={<WorkflowEditor />} />
        <Route path="workflows/new" element={<WorkflowEditor />} />
        <Route path="leads" element={<Leads />} />
        <Route path="integrations" element={<Integrations />} />
        <Route path="admin" element={<Admin />} />
      </Route>
    </Routes>
  )
}
