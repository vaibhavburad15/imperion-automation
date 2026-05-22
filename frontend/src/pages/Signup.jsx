import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Signup() {
  const { signup } = useAuth()
  const nav = useNavigate()
  const [form, setForm] = useState({ email: '', password: '', full_name: '', workspace_name: '' })
  const [err, setErr] = useState('')
  const [loading, setLoading] = useState(false)

  const submit = async (e) => {
    e.preventDefault(); setErr(''); setLoading(true)
    try { await signup(form); nav('/') }
    catch (e) { setErr(e.response?.data?.detail || 'Signup failed') }
    finally { setLoading(false) }
  }

  const upd = (k) => (e) => setForm({ ...form, [k]: e.target.value })

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-indigo-500 to-purple-600 p-4">
      <div className="bg-white rounded-2xl shadow-2xl p-8 w-full max-w-md">
        <h1 className="text-3xl font-bold text-indigo-600 mb-1">⚡ Imperion</h1>
        <p className="text-slate-500 mb-6">Create your automation workspace</p>
        <form onSubmit={submit} className="space-y-4">
          <input required placeholder="Workspace name" value={form.workspace_name} onChange={upd('workspace_name')}
                 className="w-full border border-slate-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-indigo-500" />
          <input required placeholder="Your full name" value={form.full_name} onChange={upd('full_name')}
                 className="w-full border border-slate-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-indigo-500" />
          <input required type="email" placeholder="Email" value={form.email} onChange={upd('email')}
                 className="w-full border border-slate-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-indigo-500" />
          <input required type="password" placeholder="Password (min 6)" value={form.password} onChange={upd('password')}
                 className="w-full border border-slate-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-indigo-500" />
          {err && <p className="text-red-600 text-sm">{err}</p>}
          <button disabled={loading}
                  className="w-full bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white font-medium py-2.5 rounded-lg transition">
            {loading ? 'Creating…' : 'Create workspace'}
          </button>
        </form>
        <p className="text-sm text-slate-600 text-center mt-6">
          Already have an account? <Link to="/login" className="text-indigo-600 font-medium">Sign in</Link>
        </p>
      </div>
    </div>
  )
}
