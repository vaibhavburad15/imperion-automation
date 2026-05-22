import { useEffect, useState } from 'react'
import api from '../services/api'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from 'recharts'
import { Users, Workflow, CheckCircle, AlertTriangle, Clock, TrendingUp } from 'lucide-react'

const COLORS = ['#6366f1', '#10b981', '#ef4444', '#f59e0b', '#8b5cf6']

function Stat({ icon: Icon, label, value, sub, color = 'indigo' }) {
  return (
    <div className="bg-white rounded-xl p-5 shadow-sm border border-slate-200">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-slate-500">{label}</p>
          <p className="text-2xl font-bold text-slate-800 mt-1">{value}</p>
          {sub && <p className="text-xs text-slate-400 mt-1">{sub}</p>}
        </div>
        <div className={`bg-${color}-100 text-${color}-600 p-3 rounded-lg`}>
          <Icon size={22} />
        </div>
      </div>
    </div>
  )
}

export default function Dashboard() {
  const [data, setData] = useState(null)
  const [runs, setRuns] = useState([])

  useEffect(() => {
    api.get('/analytics').then(r => setData(r.data))
    api.get('/workflows/runs/all?limit=10').then(r => setRuns(r.data))
    const intv = setInterval(() => {
      api.get('/analytics').then(r => setData(r.data))
      api.get('/workflows/runs/all?limit=10').then(r => setRuns(r.data))
    }, 10000)
    return () => clearInterval(intv)
  }, [])

  if (!data) return <div className="text-slate-500">Loading…</div>

  const statusPie = Object.entries(data.runs_by_status).map(([name, value]) => ({ name, value }))

  return (
    <div>
      <h2 className="text-2xl font-bold text-slate-800 mb-1">Dashboard</h2>
      <p className="text-slate-500 mb-6">Real-time platform analytics — refreshes every 10s</p>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <Stat icon={Users} label="Total Leads" value={data.total_leads} sub={`+${data.leads_today} today`} color="indigo" />
        <Stat icon={Workflow} label="Workflow Runs" value={data.total_runs} sub={`${data.active_workflows} active workflows`} color="purple" />
        <Stat icon={CheckCircle} label="Successful Runs" value={data.success_runs} color="emerald" />
        <Stat icon={AlertTriangle} label="Failed Runs" value={data.failed_runs} color="red" />
        <Stat icon={Clock} label="Avg Response" value={`${Math.round(data.avg_response_ms)}ms`} color="amber" />
        <Stat icon={TrendingUp} label="Conversion" value={`${data.conversion_rate}%`} color="green" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <div className="bg-white rounded-xl p-5 shadow-sm border border-slate-200">
          <h3 className="font-semibold text-slate-800 mb-4">Runs — Last 7 Days</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={data.runs_last_7_days}>
              <XAxis dataKey="date" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip />
              <Bar dataKey="count" fill="#6366f1" radius={[4,4,0,0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
        <div className="bg-white rounded-xl p-5 shadow-sm border border-slate-200">
          <h3 className="font-semibold text-slate-800 mb-4">Runs by Status</h3>
          {statusPie.length ? (
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie data={statusPie} dataKey="value" nameKey="name" innerRadius={50} outerRadius={90}>
                  {statusPie.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Pie>
                <Legend />
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          ) : <p className="text-slate-400 text-sm">No runs yet</p>}
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-slate-200">
        <h3 className="font-semibold text-slate-800 p-5 border-b border-slate-200">Recent Workflow Runs</h3>
        <table className="w-full">
          <thead className="text-xs text-slate-500 uppercase bg-slate-50">
            <tr><th className="text-left px-5 py-2">ID</th><th className="text-left px-5 py-2">Workflow</th>
                <th className="text-left px-5 py-2">Status</th><th className="text-left px-5 py-2">Duration</th>
                <th className="text-left px-5 py-2">Retries</th><th className="text-left px-5 py-2">Started</th></tr>
          </thead>
          <tbody>
            {runs.map(r => (
              <tr key={r.id} className="border-t border-slate-100 text-sm">
                <td className="px-5 py-3">#{r.id}</td>
                <td className="px-5 py-3">WF#{r.workflow_id}</td>
                <td className="px-5 py-3">
                  <span className={`px-2 py-1 rounded text-xs font-medium ${
                    r.status === 'success' ? 'bg-emerald-100 text-emerald-700' :
                    r.status === 'failed' ? 'bg-red-100 text-red-700' :
                    r.status === 'running' ? 'bg-amber-100 text-amber-700' :
                    'bg-slate-100 text-slate-700'
                  }`}>{r.status}</span>
                </td>
                <td className="px-5 py-3 text-slate-600">{r.duration_ms ? `${r.duration_ms}ms` : '—'}</td>
                <td className="px-5 py-3 text-slate-600">{r.retry_count}</td>
                <td className="px-5 py-3 text-slate-500 text-xs">{new Date(r.started_at).toLocaleString()}</td>
              </tr>
            ))}
            {!runs.length && <tr><td colSpan={6} className="text-center text-slate-400 py-8">No runs yet</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  )
}
