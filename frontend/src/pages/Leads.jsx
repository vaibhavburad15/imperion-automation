import { useEffect, useState } from 'react'
import api from '../services/api'
import { Plus, UserCheck } from 'lucide-react'

export default function Leads() {
  const [leads, setLeads] = useState([])
  const [open, setOpen] = useState(false)
  const [form, setForm] = useState({ name: '', email: '', phone: '', source: 'manual', data: {} })

  const load = () => api.get('/leads').then(r => setLeads(r.data))
  useEffect(() => { load() }, [])

  const create = async () => {
    await api.post('/leads', form)
    setOpen(false); setForm({ name:'', email:'', phone:'', source:'manual', data:{} })
    load()
  }

  const updateStatus = async (id, status) => {
    await api.put(`/leads/${id}/status?status=${status}`); load()
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-slate-800">Leads / CRM</h2>
          <p className="text-slate-500">Captured leads, scoring, and human-handoff routing</p>
        </div>
        <button onClick={() => setOpen(true)} className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-lg flex items-center gap-2">
          <Plus size={16}/> Capture Lead
        </button>
      </div>

      {open && (
        <div className="bg-white border border-slate-200 rounded-xl p-5 mb-6 grid grid-cols-1 md:grid-cols-4 gap-3">
          <input placeholder="Name" value={form.name} onChange={e=>setForm({...form, name:e.target.value})}
                 className="border border-slate-300 rounded px-3 py-2"/>
          <input placeholder="Email" value={form.email} onChange={e=>setForm({...form, email:e.target.value})}
                 className="border border-slate-300 rounded px-3 py-2"/>
          <input placeholder="Phone" value={form.phone} onChange={e=>setForm({...form, phone:e.target.value})}
                 className="border border-slate-300 rounded px-3 py-2"/>
          <input placeholder="Source" value={form.source} onChange={e=>setForm({...form, source:e.target.value})}
                 className="border border-slate-300 rounded px-3 py-2"/>
          <div className="md:col-span-4 flex justify-end gap-2">
            <button onClick={() => setOpen(false)} className="px-4 py-2 border border-slate-300 rounded-lg">Cancel</button>
            <button onClick={create} className="bg-indigo-600 text-white px-4 py-2 rounded-lg">Save & Trigger</button>
          </div>
        </div>
      )}

      <div className="bg-white rounded-xl shadow-sm border border-slate-200">
        <table className="w-full">
          <thead className="text-xs text-slate-500 uppercase bg-slate-50">
            <tr>
              <th className="text-left px-5 py-3">Name</th>
              <th className="text-left px-5 py-3">Email</th>
              <th className="text-left px-5 py-3">Source</th>
              <th className="text-left px-5 py-3">Score</th>
              <th className="text-left px-5 py-3">Status</th>
              <th className="text-left px-5 py-3">Created</th>
            </tr>
          </thead>
          <tbody>
            {leads.map(l => (
              <tr key={l.id} className="border-t border-slate-100 text-sm">
                <td className="px-5 py-3 font-medium">{l.name || '—'} {l.requires_human && <UserCheck size={14} className="inline text-orange-500" title="Human handoff"/>}</td>
                <td className="px-5 py-3 text-slate-600">{l.email}</td>
                <td className="px-5 py-3"><span className="px-2 py-1 bg-slate-100 rounded text-xs">{l.source}</span></td>
                <td className="px-5 py-3">
                  <div className="flex items-center gap-2">
                    <div className="w-20 bg-slate-200 rounded-full h-2"><div className="bg-indigo-600 h-2 rounded-full" style={{width:`${l.score}%`}}/></div>
                    <span className="text-xs">{l.score.toFixed(0)}</span>
                  </div>
                </td>
                <td className="px-5 py-3">
                  <select value={l.status} onChange={e=>updateStatus(l.id, e.target.value)}
                          className="text-xs border border-slate-300 rounded px-2 py-1">
                    <option>new</option><option>contacted</option><option>qualified</option>
                    <option>converted</option><option>lost</option>
                  </select>
                </td>
                <td className="px-5 py-3 text-xs text-slate-500">{new Date(l.created_at).toLocaleString()}</td>
              </tr>
            ))}
            {!leads.length && <tr><td colSpan={6} className="text-center text-slate-400 py-10">No leads yet</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  )
}
