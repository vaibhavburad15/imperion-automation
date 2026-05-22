import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { LayoutDashboard, Workflow, Users, Plug, ShieldCheck, LogOut } from 'lucide-react'

export default function Layout() {
  const { user, logout } = useAuth()
  const nav = useNavigate()

  const linkClass = ({ isActive }) =>
    `flex items-center gap-3 px-4 py-2.5 rounded-lg transition ${
      isActive ? 'bg-indigo-600 text-white' : 'text-slate-700 hover:bg-slate-100'
    }`

  return (
    <div className="flex min-h-screen">
      <aside className="w-64 bg-white border-r border-slate-200 p-4 flex flex-col">
        <div className="mb-8 px-2">
          <h1 className="text-xl font-bold text-indigo-600">⚡ Imperion</h1>
          <p className="text-xs text-slate-500 mt-1">Automation Platform</p>
        </div>
        <nav className="flex-1 space-y-1">
          <NavLink to="/" end className={linkClass}>
            <LayoutDashboard size={18} /> Dashboard
          </NavLink>
          <NavLink to="/workflows" className={linkClass}>
            <Workflow size={18} /> Workflows
          </NavLink>
          <NavLink to="/leads" className={linkClass}>
            <Users size={18} /> Leads / CRM
          </NavLink>
          <NavLink to="/integrations" className={linkClass}>
            <Plug size={18} /> Integrations
          </NavLink>
          <NavLink to="/admin" className={linkClass}>
            <ShieldCheck size={18} /> Admin
          </NavLink>
        </nav>
        <div className="border-t border-slate-200 pt-4 mt-4">
          <p className="text-sm font-medium text-slate-800 truncate">{user?.email}</p>
          <p className="text-xs text-slate-500">Workspace #{user?.workspace_id}</p>
          <button
            onClick={() => { logout(); nav('/login') }}
            className="mt-3 w-full flex items-center gap-2 px-3 py-2 text-sm text-slate-700 hover:bg-slate-100 rounded-lg"
          >
            <LogOut size={16} /> Logout
          </button>
        </div>
      </aside>
      <main className="flex-1 p-8 overflow-auto">
        <Outlet />
      </main>
    </div>
  )
}
