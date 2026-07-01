import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Shield, UserPlus } from 'lucide-react'
import api from '../utils/api'
import { useAuthStore } from '../store/authStore'
import toast from 'react-hot-toast'

export default function RegisterPage() {
  const [form, setForm] = useState({ email: '', password: '', full_name: '' })
  const [loading, setLoading] = useState(false)
  const { setAuth } = useAuthStore()
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      const { data } = await api.post('/auth/register', form)
      setAuth(data.user, data.access_token)
      toast.success('Account created!')
      navigate('/')
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Registration failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="w-16 h-16 rounded-2xl bg-blue-600 flex items-center justify-center mx-auto mb-4">
            <Shield size={32} className="text-white" />
          </div>
          <h1 className="text-3xl font-bold text-white mb-2">DocuTrust AI</h1>
          <p className="text-slate-400">Create your account</p>
        </div>
        <div className="card">
          <h2 className="text-xl font-semibold text-white mb-6">Get Started</h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="text-sm text-slate-400 mb-1 block">Full Name</label>
              <input type="text" className="input-field" placeholder="Jane Smith"
                value={form.full_name} onChange={(e) => setForm({...form, full_name: e.target.value})} />
            </div>
            <div>
              <label className="text-sm text-slate-400 mb-1 block">Email</label>
              <input type="email" required className="input-field" placeholder="you@company.com"
                value={form.email} onChange={(e) => setForm({...form, email: e.target.value})} />
            </div>
            <div>
              <label className="text-sm text-slate-400 mb-1 block">Password</label>
              <input type="password" required className="input-field" placeholder="Min 8 characters"
                value={form.password} onChange={(e) => setForm({...form, password: e.target.value})} />
            </div>
            <button type="submit" disabled={loading} className="btn-primary w-full justify-center mt-6">
              <UserPlus size={18} /> {loading ? 'Creating...' : 'Create Account'}
            </button>
          </form>
          <p className="text-center text-slate-400 text-sm mt-4">
            Have an account? <Link to="/login" className="text-blue-400 hover:text-blue-300">Sign in</Link>
          </p>
        </div>
      </div>
    </div>
  )
}
