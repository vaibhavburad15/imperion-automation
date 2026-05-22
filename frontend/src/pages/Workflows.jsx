import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../services/api'
import { Plus, Play, Trash2, RotateCcw, Sparkles } from 'lucide-react'

export default function Workflows() {
  const [wfs, setWfs] = useState([])
  const [aiOpen, setAiOpen] = useState(false)
  const [aiDesc, setAiDesc] = useState('')
  const [aiLoading, setAiLoading] = useState(false)

  const load = () => api.get('/workflows').then(r => setWfs(r.data))
  useEffect(() => { load() }, [])

  const run = async (id) => {
    await api.post(`/workflows/${id}/run`, { payload: { name: 'Demo Lead', email: 'demo@example.com', phone: '+10000', source: 'manual' } })
    alert('Run triggered! Check the Dashboard.')
  }
  const del = async (id) => {
    if (!confirm('Delete this workflow?')) return
    await api.delete(`/workflows/${id}`); load()
  }
  const rollback = async (id) => {
    if (!confirm('Roll back to previous version?')) return
    await api.post(`/workflows/${id}/rollback`); load()
  }

  const aiGenerate = async () => {
    setAiLoading(true)
    try {
      const { data } = await api.post('/ai/generate-workflow', { description: aiDesc })
      await api.post('/workflows', data)
      setAiOpen(false); setAiDesc(''); load()
    } catch (e) { alert('AI generation failed: ' + (e.response?.data?.detail || e.message)) }
    finally { setAiLoading(false) }
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-slate-800">Workflows</h2>
          <p className="text-slate-500">Build trigger → condition → action → follow-up chains</p>
        </div>
        <div className="flex gap-2">
          <button onClick={() => setAiOpen(true)} className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg flex items-center gap-2">
            <Sparkles size={16}/> AI Generate
          </button>
          <Link to="/workflows/new" className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-lg flex items-center gap-2">
            <Plus size={16}/> New Workflow
          </Link>
        </div>
      </div>

      {aiOpen && (
        <div className="bg-purple-50 border border-purple-200 rounded-xl p-5 mb-6">
          <h3 className="font-semibold text-purple-900 mb-2">✨ AI Workflow Generator</h3>
          <p className="text-sm text-purple-700 mb-3">Describe what you want in plain English. Try: "When a new lead arrives, save to CRM, send welcome email and Slack alert"</p>
          <textarea rows={3} value={aiDesc} onChange={e => setAiDesc(e.target.value)}
                    className="w-full border border-purple-300 rounded-lg p-3 text-sm" placeholder="Describe your workflow…"/>
          <div className="flex gap-2 mt-3">
            <button disabled={aiLoading || !aiDesc} onClick={aiGenerate}
                    className="bg-purple-600 hover:bg-purple-700 disabled:opacity-50 text-white px-4 py-2 rounded-lg">
              {aiLoading ? 'Generating…' : 'Generate & Save'}
            </button>
            <button onClick={() => setAiOpen(false)} className="px-4 py-2 rounded-lg border border-slate-300">Cancel</button>
          </div>
        </div>
      )}

      <div className="bg-white rounded-xl shadow-sm border border-slate-200">
        <table className="w-full">
          <thead className="text-xs text-slate-500 uppercase bg-slate-50">
            <tr>
              <th className="text-left px-5 py-3">Name</th>
              <th className="text-left px-5 py-3">Trigger</th>
              <th className="text-left px-5 py-3">Nodes</th>
              <th className="text-left px-5 py-3">Version</th>
              <th className="text-left px-5 py-3">Status</th>
              <th className="text-right px-5 py-3">Actions</th>
            </tr>
          </thead>
          <tbody>
            {wfs.map(w => (
              <tr key={w.id} className="border-t border-slate-100 text-sm">
                <td className="px-5 py-3"><Link to={`/workflows/${w.id}`} className="font-medium text-indigo-600 hover:underline">{w.name}</Link><p className="text-xs text-slate-500">{w.description}</p></td>
                <td className="px-5 py-3"><span className="px-2 py-1 bg-slate-100 rounded text-xs">{w.trigger_type}</span></td>
                <td className="px-5 py-3 text-slate-600">{w.graph?.nodes?.length || 0}</td>
                <td className="px-5 py-3 text-slate-600">v{w.version}</td>
                <td className="px-5 py-3">
                  <span className={`px-2 py-1 rounded text-xs ${w.is_active ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-500'}`}>
                    {w.is_active ? 'active' : 'inactive'}
                  </span>
                </td>
                <td className="px-5 py-3 text-right space-x-2">
                  <button onClick={() => run(w.id)} className="inline-flex items-center gap-1 text-emerald-600 hover:bg-emerald-50 px-2 py-1 rounded text-xs"><Play size={12}/> Run</button>
                  <button onClick={() => rollback(w.id)} className="inline-flex items-center gap-1 text-amber-600 hover:bg-amber-50 px-2 py-1 rounded text-xs"><RotateCcw size={12}/> Rollback</button>
                  <button onClick={() => del(w.id)} className="inline-flex items-center gap-1 text-red-600 hover:bg-red-50 px-2 py-1 rounded text-xs"><Trash2 size={12}/> Delete</button>
                </td>
              </tr>
            ))}
            {!wfs.length && <tr><td colSpan={6} className="text-center text-slate-400 py-10">No workflows yet — click "New Workflow" or "AI Generate"</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  )
}
