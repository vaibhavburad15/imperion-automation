import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import api from '../services/api'
import { Save, ArrowRight } from 'lucide-react'

const DEFAULT_GRAPH = {
  nodes: [
    { id: 't1', type: 'trigger', label: 'Trigger', next: 'a1' },
    { id: 'a1', type: 'action', label: 'Save to CRM',
      config: { provider: 'crm', action: 'upsert_lead' }, next: null },
  ],
}

export default function WorkflowEditor() {
  const { id } = useParams()
  const nav = useNavigate()
  const isNew = !id
  const [wf, setWf] = useState({
    name: 'My Workflow', description: '',
    trigger_type: 'lead_created', trigger_config: {},
    graph: DEFAULT_GRAPH, is_active: true,
  })
  const [graphText, setGraphText] = useState(JSON.stringify(DEFAULT_GRAPH, null, 2))
  const [err, setErr] = useState('')

  useEffect(() => {
    if (!isNew) {
      api.get(`/workflows/${id}`).then(r => {
        setWf(r.data); setGraphText(JSON.stringify(r.data.graph, null, 2))
      })
    }
  }, [id])

  const save = async () => {
    setErr('')
    let graph
    try { graph = JSON.parse(graphText) }
    catch (e) { setErr('Graph JSON is invalid: ' + e.message); return }
    const body = { ...wf, graph }
    try {
      if (isNew) { const r = await api.post('/workflows', body); nav(`/workflows/${r.data.id}`) }
      else { await api.put(`/workflows/${id}`, body); alert('Saved (new version)') }
    } catch (e) { setErr(e.response?.data?.detail || e.message) }
  }

  return (
    <div>
      <h2 className="text-2xl font-bold text-slate-800 mb-1">{isNew ? 'New' : 'Edit'} Workflow</h2>
      <p className="text-slate-500 mb-6">Define your trigger → condition → action chain</p>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1 space-y-4">
          <div className="bg-white rounded-xl border border-slate-200 p-5">
            <label className="block text-sm font-medium text-slate-700 mb-1">Name</label>
            <input value={wf.name} onChange={e=>setWf({...wf,name:e.target.value})}
                   className="w-full border border-slate-300 rounded-lg px-3 py-2 mb-3"/>
            <label className="block text-sm font-medium text-slate-700 mb-1">Description</label>
            <textarea rows={3} value={wf.description || ''} onChange={e=>setWf({...wf,description:e.target.value})}
                   className="w-full border border-slate-300 rounded-lg px-3 py-2 mb-3"/>
            <label className="block text-sm font-medium text-slate-700 mb-1">Trigger Type</label>
            <select value={wf.trigger_type} onChange={e=>setWf({...wf,trigger_type:e.target.value})}
                    className="w-full border border-slate-300 rounded-lg px-3 py-2 mb-3">
              <option value="manual">Manual</option>
              <option value="lead_created">Lead Created</option>
              <option value="webhook">Webhook</option>
              <option value="schedule">Schedule</option>
            </select>
            {wf.trigger_type === 'schedule' && (
              <input placeholder="every:300 (seconds)"
                     onChange={e=>setWf({...wf, trigger_config:{interval: e.target.value}})}
                     className="w-full border border-slate-300 rounded-lg px-3 py-2 mb-3"/>
            )}
            <label className="flex items-center gap-2 text-sm">
              <input type="checkbox" checked={wf.is_active} onChange={e=>setWf({...wf, is_active:e.target.checked})}/>
              Active
            </label>
          </div>

          <div className="bg-indigo-50 border border-indigo-200 rounded-xl p-4 text-xs text-indigo-900">
            <p className="font-semibold mb-2">Quick Reference — Node types</p>
            <ul className="space-y-1 list-disc list-inside">
              <li><b>trigger</b>: entry point</li>
              <li><b>action</b>: call integration (provider + action)</li>
              <li><b>condition</b>: branch on context field</li>
              <li><b>follow_up</b>: delayed action</li>
              <li><b>delay</b>: pause N seconds</li>
            </ul>
            <p className="font-semibold mt-3 mb-1">Providers</p>
            <p>crm, email, slack, telegram, whatsapp, sheets, calendar, webhook</p>
            <p className="font-semibold mt-3 mb-1">Templating</p>
            <p>Use <code>{'{{name}}'}</code>, <code>{'{{email}}'}</code> in strings</p>
          </div>
        </div>

        <div className="lg:col-span-2">
          <div className="bg-white rounded-xl border border-slate-200 p-5">
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-semibold text-slate-800">Graph (JSON)</h3>
              <button onClick={save} className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-lg flex items-center gap-2">
                <Save size={16}/> Save Workflow
              </button>
            </div>
            <textarea rows={20} value={graphText} onChange={e=>setGraphText(e.target.value)}
                      className="w-full font-mono text-xs border border-slate-300 rounded-lg p-3"/>
            {err && <p className="text-red-600 text-sm mt-2">{err}</p>}
          </div>

          {wf.graph?.nodes && (
            <div className="mt-4 bg-white rounded-xl border border-slate-200 p-5">
              <h3 className="font-semibold text-slate-800 mb-3">Visual Preview</h3>
              <div className="flex flex-wrap items-center gap-2">
                {wf.graph.nodes.map((n, i) => (
                  <div key={n.id} className="flex items-center gap-2">
                    <div className={`px-3 py-2 rounded-lg text-sm border-2 ${
                      n.type === 'trigger' ? 'bg-amber-50 border-amber-300 text-amber-800' :
                      n.type === 'condition' ? 'bg-blue-50 border-blue-300 text-blue-800' :
                      n.type === 'follow_up' ? 'bg-purple-50 border-purple-300 text-purple-800' :
                      'bg-emerald-50 border-emerald-300 text-emerald-800'
                    }`}>
                      <div className="font-medium">{n.label || n.id}</div>
                      <div className="text-xs opacity-70">{n.type} {n.config?.provider && `· ${n.config.provider}`}</div>
                    </div>
                    {i < wf.graph.nodes.length - 1 && <ArrowRight size={16} className="text-slate-400"/>}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
