import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Login() {
  const { login } = useAuth()
  const nav = useNavigate()
  const [email, setEmail] = useState('admin@acme.com')
  const [password, setPassword] = useState('password123')
  const [err, setErr] = useState('')
  const [loading, setLoading] = useState(false)

  const submit = async (e) => {
    e.preventDefault(); setErr(''); setLoading(true)
    try { await login(email, password); nav('/') }
    catch (e) { setErr(e.response?.data?.detail || 'Login failed') }
    finally { setLoading(false) }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-indigo-500 to-purple-600 p-4">
      <div className="bg-white rounded-2xl shadow-2xl p-8 w-full max-w-md">
        <h1 className="text-3xl font-bold text-indigo-600 mb-1">⚡ Imperion</h1>
        <p className="text-slate-500 mb-6">Sign in to your automation workspace</p>
        <form onSubmit={submit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Email</label>
            <input type="email" required value={email} onChange={e=>setEmail(e.target.value)}
                   className="w-full border border-slate-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-indigo-500" />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Password</label>
            <input type="password" required value={password} onChange={e=>setPassword(e.target.value)}
                   className="w-full border border-slate-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-indigo-500" />
          </div>
          {err && <p className="text-red-600 text-sm">{err}</p>}
          <button disabled={loading}
                  className="w-full bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white font-medium py-2.5 rounded-lg transition">
            {loading ? 'Signing in…' : 'Sign in'}
          </button>
        </form>
        <p className="text-sm text-slate-600 text-center mt-6">
          New here? <Link to="/signup" className="text-indigo-600 font-medium">Create workspace</Link>
        </p>
        <div className="mt-6 bg-slate-50 rounded-lg p-3 text-xs text-slate-600">
          <p className="font-medium mb-1">Demo credentials:</p>
          <p>admin@acme.com / password123</p>
          <p>admin@globex.com / password123</p>
        </div>
      </div>
    </div>
  )
}
