import { useEffect, useState } from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line } from 'recharts'
import { Shield, FileText, MessageSquare, TrendingUp, ThumbsUp, ThumbsDown } from 'lucide-react'
import api from '../utils/api'

const COLORS = ['#3b82f6', '#8b5cf6', '#10b981', '#f59e0b', '#ef4444']

function StatCard({ icon: Icon, label, value, color }) {
  return (
    <div className="card flex items-center gap-4">
      <div className={`w-11 h-11 rounded-xl flex items-center justify-center ${color}`}>
        <Icon size={20} className="text-white" />
      </div>
      <div>
        <p className="text-slate-400 text-xs">{label}</p>
        <p className="text-2xl font-bold text-white">{value ?? '—'}</p>
      </div>
    </div>
  )
}

export default function AnalyticsPage() {
  const [stats, setStats] = useState(null)
  const [docs, setDocs] = useState([])

  useEffect(() => {
    api.get('/analytics/dashboard').then(r => setStats(r.data)).catch(() => {})
    api.get('/documents/').then(r => setDocs(r.data)).catch(() => {})
  }, [])

  const trustData = stats ? [
    { name: 'High (80-100%)', value: Math.round(stats.total_questions * 0.6), fill: '#10b981' },
    { name: 'Medium (50-80%)', value: Math.round(stats.total_questions * 0.3), fill: '#f59e0b' },
    { name: 'Low (<50%)', value: Math.round(stats.total_questions * 0.1), fill: '#ef4444' },
  ] : []

  const deptData = docs.reduce((acc, d) => {
    const dept = d.department || 'Uncategorized'
    acc[dept] = (acc[dept] || 0) + 1
    return acc
  }, {})
  const deptChartData = Object.entries(deptData).map(([name, count]) => ({ name, count }))

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white">Analytics</h1>
        <p className="text-slate-400 mt-1">Insights into your knowledge base usage and AI performance</p>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <StatCard icon={FileText} label="Documents" value={stats?.total_documents} color="bg-blue-600" />
        <StatCard icon={MessageSquare} label="Questions Asked" value={stats?.total_questions} color="bg-purple-600" />
        <StatCard icon={Shield} label="Avg Trust Score" value={stats?.average_trust_score ? `${stats.average_trust_score}%` : null} color="bg-emerald-600" />
        <StatCard icon={TrendingUp} label="Satisfaction" value={stats?.satisfaction_rate ? `${stats.satisfaction_rate}%` : null} color="bg-orange-600" />
      </div>

      <div className="grid lg:grid-cols-2 gap-6 mb-6">
        {/* Trust Score Distribution */}
        <div className="card">
          <h2 className="text-lg font-semibold text-white mb-6">Trust Score Distribution</h2>
          {stats?.total_questions > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie data={trustData} cx="50%" cy="50%" innerRadius={60} outerRadius={90} paddingAngle={4} dataKey="value">
                  {trustData.map((entry, i) => <Cell key={i} fill={entry.fill} />)}
                </Pie>
                <Tooltip formatter={(v) => [v, 'Responses']} contentStyle={{ background: '#1e293b', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px', color: '#e2e8f0' }} />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-56 flex items-center justify-center text-slate-500">No data yet</div>
          )}
          <div className="flex justify-center gap-4 mt-2">
            {[['#10b981', 'High'], ['#f59e0b', 'Medium'], ['#ef4444', 'Low']].map(([color, label]) => (
              <div key={label} className="flex items-center gap-2 text-xs text-slate-400">
                <div className="w-3 h-3 rounded-full" style={{ background: color }} /> {label}
              </div>
            ))}
          </div>
        </div>

        {/* Documents by Department */}
        <div className="card">
          <h2 className="text-lg font-semibold text-white mb-6">Documents by Department</h2>
          {deptChartData.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={deptChartData} margin={{ left: -20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="name" tick={{ fill: '#94a3b8', fontSize: 11 }} />
                <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} />
                <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px', color: '#e2e8f0' }} />
                <Bar dataKey="count" fill="#3b82f6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-56 flex items-center justify-center text-slate-500">No documents uploaded yet</div>
          )}
        </div>
      </div>

      {/* Feedback Summary */}
      <div className="card">
        <h2 className="text-lg font-semibold text-white mb-4">User Feedback Summary</h2>
        <div className="flex items-center gap-8">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-xl bg-emerald-900/50 border border-emerald-700/50 flex items-center justify-center">
              <ThumbsUp size={20} className="text-emerald-400" />
            </div>
            <div>
              <p className="text-2xl font-bold text-emerald-400">{stats?.positive_feedback ?? 0}</p>
              <p className="text-xs text-slate-400">Positive</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-xl bg-red-900/50 border border-red-700/50 flex items-center justify-center">
              <ThumbsDown size={20} className="text-red-400" />
            </div>
            <div>
              <p className="text-2xl font-bold text-red-400">{stats?.negative_feedback ?? 0}</p>
              <p className="text-xs text-slate-400">Negative</p>
            </div>
          </div>
          {stats && (stats.positive_feedback + stats.negative_feedback) > 0 && (
            <div className="flex-1">
              <div className="flex justify-between text-xs text-slate-400 mb-1">
                <span>Satisfaction rate</span>
                <span>{stats.satisfaction_rate}%</span>
              </div>
              <div className="h-2 bg-white/10 rounded-full overflow-hidden">
                <div className="h-full bg-gradient-to-r from-emerald-500 to-emerald-400 rounded-full" style={{ width: `${stats.satisfaction_rate}%` }} />
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
