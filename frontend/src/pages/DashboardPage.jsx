import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { FileText, MessageSquare, Shield, TrendingUp, Upload, ArrowRight, CheckCircle, Clock, AlertCircle } from 'lucide-react'
import { useAuthStore } from '../store/authStore'
import api from '../utils/api'

function StatCard({ icon: Icon, label, value, color, sub }) {
  return (
    <div className="card flex items-start gap-4">
      <div className={`w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0 ${color}`}>
        <Icon size={22} className="text-white" />
      </div>
      <div>
        <p className="text-slate-400 text-sm">{label}</p>
        <p className="text-3xl font-bold text-white mt-0.5">{value}</p>
        {sub && <p className="text-xs text-slate-500 mt-1">{sub}</p>}
      </div>
    </div>
  )
}

function TrustBadge({ score }) {
  const color = score >= 80 ? 'text-emerald-400' : score >= 50 ? 'text-amber-400' : 'text-red-400'
  return <span className={`font-bold ${color}`}>{score}%</span>
}

export default function DashboardPage() {
  const { user } = useAuthStore()
  const [stats, setStats] = useState(null)
  const [docs, setDocs] = useState([])
  const [chats, setChats] = useState([])

  useEffect(() => {
    api.get('/analytics/dashboard').then(r => setStats(r.data)).catch(() => {})
    api.get('/documents/').then(r => setDocs(r.data.slice(0, 5))).catch(() => {})
    api.get('/chat/history').then(r => setChats(r.data.slice(0, 5))).catch(() => {})
  }, [])

  const statusIcon = (s) => s === 'ready'
    ? <CheckCircle size={14} className="text-emerald-400" />
    : s === 'processing'
    ? <Clock size={14} className="text-amber-400 animate-spin" />
    : <AlertCircle size={14} className="text-red-400" />

  return (
    <div className="p-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white">
          Good {new Date().getHours() < 12 ? 'Morning' : new Date().getHours() < 17 ? 'Afternoon' : 'Evening'}, {user?.full_name?.split(' ')[0]} 👋
        </h1>
        <p className="text-slate-400 mt-1">Here's what's happening in your knowledge base today.</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <StatCard icon={FileText} label="Total Documents" value={stats?.total_documents ?? '—'} color="bg-blue-600" sub={`${stats?.ready_documents ?? 0} ready`} />
        <StatCard icon={MessageSquare} label="Questions Asked" value={stats?.total_questions ?? '—'} color="bg-purple-600" />
        <StatCard icon={Shield} label="Avg Trust Score" value={stats?.average_trust_score ? `${stats.average_trust_score}%` : '—'} color="bg-emerald-600" />
        <StatCard icon={TrendingUp} label="Satisfaction" value={stats?.satisfaction_rate ? `${stats.satisfaction_rate}%` : '—'} color="bg-orange-600" sub={`${stats?.positive_feedback ?? 0} 👍  ${stats?.negative_feedback ?? 0} 👎`} />
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        {/* Recent Documents */}
        <div className="card">
          <div className="flex items-center justify-between mb-5">
            <h2 className="text-lg font-semibold text-white">Recent Documents</h2>
            <Link to="/upload" className="text-blue-400 text-sm hover:text-blue-300 flex items-center gap-1">
              Upload <ArrowRight size={14} />
            </Link>
          </div>
          {docs.length === 0 ? (
            <div className="text-center py-10">
              <Upload size={32} className="text-slate-600 mx-auto mb-3" />
              <p className="text-slate-400 text-sm">No documents yet</p>
              <Link to="/upload" className="btn-primary mt-3 inline-flex text-sm">Upload your first PDF</Link>
            </div>
          ) : (
            <div className="space-y-3">
              {docs.map(doc => (
                <div key={doc.id} className="flex items-center gap-3 p-3 rounded-lg bg-white/5 hover:bg-white/10 transition-all">
                  <FileText size={16} className="text-blue-400 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-white truncate">{doc.title}</p>
                    <p className="text-xs text-slate-400">{doc.page_count} pages · v{doc.version}</p>
                  </div>
                  <div className="flex items-center gap-1 text-xs text-slate-400">
                    {statusIcon(doc.status)} <span className="capitalize">{doc.status}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Recent Chats */}
        <div className="card">
          <div className="flex items-center justify-between mb-5">
            <h2 className="text-lg font-semibold text-white">Recent Chats</h2>
            <Link to="/workspace" className="text-blue-400 text-sm hover:text-blue-300 flex items-center gap-1">
              Open <ArrowRight size={14} />
            </Link>
          </div>
          {chats.length === 0 ? (
            <div className="text-center py-10">
              <MessageSquare size={32} className="text-slate-600 mx-auto mb-3" />
              <p className="text-slate-400 text-sm">No conversations yet</p>
              <Link to="/workspace" className="btn-primary mt-3 inline-flex text-sm">Start asking questions</Link>
            </div>
          ) : (
            <div className="space-y-3">
              {chats.map(chat => (
                <Link to={`/workspace?chat=${chat.id}`} key={chat.id}
                  className="flex items-center gap-3 p-3 rounded-lg bg-white/5 hover:bg-white/10 transition-all block">
                  <MessageSquare size={16} className="text-purple-400 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-white truncate">{chat.title}</p>
                    <p className="text-xs text-slate-400">{new Date(chat.created_at).toLocaleDateString()}</p>
                  </div>
                  <ArrowRight size={14} className="text-slate-600" />
                </Link>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Quick actions */}
      <div className="mt-6 grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { to: '/upload', icon: Upload, label: 'Upload PDF', color: 'from-blue-600 to-blue-700' },
          { to: '/workspace', icon: MessageSquare, label: 'Ask AI', color: 'from-purple-600 to-purple-700' },
          { to: '/analytics', icon: TrendingUp, label: 'Analytics', color: 'from-emerald-600 to-emerald-700' },
          { to: '/workspace', icon: Shield, label: 'Trust Reports', color: 'from-orange-600 to-orange-700' },
        ].map(({ to, icon: Icon, label, color }) => (
          <Link key={label} to={to}
            className={`flex flex-col items-center gap-3 p-5 rounded-xl bg-gradient-to-br ${color} hover:opacity-90 transition-all`}>
            <Icon size={24} className="text-white" />
            <span className="text-sm font-medium text-white">{label}</span>
          </Link>
        ))}
      </div>
    </div>
  )
}
