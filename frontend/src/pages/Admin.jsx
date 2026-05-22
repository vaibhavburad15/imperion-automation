import { useEffect, useState } from 'react'
import api from '../services/api'

export default function Admin() {
  const [audit, setAudit] = useState([])
  const [events, setEvents] = useState([])
  const [tab, setTab] = useState('audit')

  useEffect(() => {
    api.get('/analytics/audit-logs?limit=200').then(r => setAudit(r.data))
    api.get('/webhooks/events?limit=100').then(r => setEvents(r.data))
  }, [])

  const replay = async (id) => {
    await api.post(`/webhooks/events/${id}/replay`); alert('Replay queued')
  }

  return (
    <div>
      <h2 className="text-2xl font-bold text-slate-800 mb-1">Admin Panel</h2>
      <p className="text-slate-500 mb-6">Audit logs, webhook events, and reliability controls</p>

      <div className="flex gap-2 mb-4">
        <button onClick={() => setTab('audit')}
                className={`px-4 py-2 rounded-lg ${tab==='audit'?'bg-indigo-600 text-white':'bg-white border border-slate-300'}`}>
          Audit Logs ({audit.length})
        </button>
        <button onClick={() => setTab('events')}
                className={`px-4 py-2 rounded-lg ${tab==='events'?'bg-indigo-600 text-white':'bg-white border border-slate-300'}`}>
          Webhook Events ({events.length})
        </button>
      </div>

      {tab === 'audit' && (
        <div className="bg-white rounded-xl shadow-sm border border-slate-200">
          <table className="w-full">
            <thead className="text-xs text-slate-500 uppercase bg-slate-50">
              <tr><th className="text-left px-5 py-3">Time</th><th className="text-left px-5 py-3">Actor</th>
                  <th className="text-left px-5 py-3">Action</th><th className="text-left px-5 py-3">Resource</th>
                  <th className="text-left px-5 py-3">Details</th></tr>
            </thead>
            <tbody>
              {audit.map(a => (
                <tr key={a.id} className="border-t border-slate-100 text-sm">
                  <td className="px-5 py-3 text-xs text-slate-500">{new Date(a.created_at).toLocaleString()}</td>
                  <td className="px-5 py-3 text-slate-700">{a.actor}</td>
                  <td className="px-5 py-3"><span className="px-2 py-1 bg-indigo-50 text-indigo-700 rounded text-xs">{a.action}</span></td>
                  <td className="px-5 py-3 text-slate-600">{a.resource_type} #{a.resource_id}</td>
                  <td className="px-5 py-3 text-xs text-slate-500 truncate max-w-xs">{JSON.stringify(a.details)}</td>
                </tr>
              ))}
              {!audit.length && <tr><td colSpan={5} className="text-center text-slate-400 py-10">No audit entries yet</td></tr>}
            </tbody>
          </table>
        </div>
      )}

      {tab === 'events' && (
        <div className="bg-white rounded-xl shadow-sm border border-slate-200">
          <table className="w-full">
            <thead className="text-xs text-slate-500 uppercase bg-slate-50">
              <tr><th className="text-left px-5 py-3">Time</th><th className="text-left px-5 py-3">Source</th>
                  <th className="text-left px-5 py-3">Workflow</th><th className="text-left px-5 py-3">Processed</th>
                  <th className="text-left px-5 py-3">Payload</th><th></th></tr>
            </thead>
            <tbody>
              {events.map(e => (
                <tr key={e.id} className="border-t border-slate-100 text-sm">
                  <td className="px-5 py-3 text-xs text-slate-500">{new Date(e.received_at).toLocaleString()}</td>
                  <td className="px-5 py-3">{e.source}</td>
                  <td className="px-5 py-3">WF#{e.workflow_id}</td>
                  <td className="px-5 py-3">{e.processed?'✅':'⏳'}</td>
                  <td className="px-5 py-3 text-xs text-slate-500 truncate max-w-xs">{JSON.stringify(e.payload)}</td>
                  <td className="px-5 py-3"><button onClick={()=>replay(e.id)} className="text-xs text-indigo-600 hover:underline">Replay</button></td>
                </tr>
              ))}
              {!events.length && <tr><td colSpan={6} className="text-center text-slate-400 py-10">No webhook events received</td></tr>}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
