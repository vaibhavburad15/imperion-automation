import { useEffect, useState } from 'react'
import api from '../services/api'
import { Plus, Trash2, CheckCircle, Plug } from 'lucide-react'

const PROVIDERS = ['email','gmail','slack','telegram','whatsapp','sheets','crm','calendar','webhook']

export default function Integrations() {
  const [integs, setIntegs] = useState([])
  const [open, setOpen] = useState(false)
  const [form, setForm] = useState({ provider:'email', name:'', config:'{}' })

  const load = () => api.get('/integrations').then(r => setIntegs(r.data))
  useEffect(() => { load() }, [])

  const create = async () => {
    let cfg = {}; try { cfg = JSON.parse(form.config) } catch { alert('Config must be valid JSON'); return }
    await api.post('/integrations', { provider: form.provider, name: form.name || form.provider, config: cfg })
    setOpen(false); setForm({ provider:'email', name:'', config:'{}' }); load()
  }

  const del = async (id) => {
    if (!confirm('Delete integration?')) return
    await api.delete(`/integrations/${id}`); load()
  }

  const test = async (id) => {
    const { data } = await api.post(`/integrations/${id}/test`)
    alert(data.success ? '✅ Test OK: ' + JSON.stringify(data.result) : '❌ ' + data.error)
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-slate-800">Integrations</h2>
          <p className="text-slate-500">Connect external services to your workflows</p>
        </div>
        <button onClick={() => setOpen(true)} className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-lg flex items-center gap-2">
          <Plus size={16}/> Add Integration
        </button>
      </div>

      {open && (
        <div className="bg-white border border-slate-200 rounded-xl p-5 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-3">
            <select value={form.provider} onChange={e=>setForm({...form, provider:e.target.value})}
                    className="border border-slate-300 rounded px-3 py-2">
              {PROVIDERS.map(p => <option key={p}>{p}</option>)}
            </select>
            <input placeholder="Name" value={form.name} onChange={e=>setForm({...form, name:e.target.value})}
                   className="border border-slate-300 rounded px-3 py-2"/>
          </div>
          <label className="text-sm text-slate-600 mb-1 block">Config (JSON — credentials/URLs/etc.)</label>
          <textarea rows={4} value={form.config} onChange={e=>setForm({...form, config:e.target.value})}
                    className="w-full font-mono text-xs border border-slate-300 rounded p-3"/>
          <div className="flex justify-end gap-2 mt-3">
            <button onClick={() => setOpen(false)} className="px-4 py-2 border border-slate-300 rounded-lg">Cancel</button>
            <button onClick={create} className="bg-indigo-600 text-white px-4 py-2 rounded-lg">Save</button>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {integs.map(i => (
          <div key={i.id} className="bg-white border border-slate-200 rounded-xl p-5">
            <div className="flex items-start justify-between mb-3">
              <div className="bg-indigo-100 text-indigo-600 p-2 rounded-lg"><Plug size={20}/></div>
              <span className={`px-2 py-1 rounded text-xs ${i.is_active?'bg-emerald-100 text-emerald-700':'bg-slate-100 text-slate-500'}`}>
                {i.is_active?'active':'disabled'}
              </span>
            </div>
            <h3 className="font-semibold text-slate-800">{i.name}</h3>
            <p className="text-xs text-slate-500 mb-3">{i.provider}</p>
            <div className="flex gap-2">
              <button onClick={() => test(i.id)} className="flex items-center gap-1 text-xs text-emerald-600 hover:bg-emerald-50 px-2 py-1 rounded">
                <CheckCircle size={12}/> Test
              </button>
              <button onClick={() => del(i.id)} className="flex items-center gap-1 text-xs text-red-600 hover:bg-red-50 px-2 py-1 rounded">
                <Trash2 size={12}/> Delete
              </button>
            </div>
          </div>
        ))}
        {!integs.length && <p className="text-slate-400 col-span-full text-center py-10">No integrations connected — click "Add Integration"</p>}
      </div>
    </div>
  )
}
