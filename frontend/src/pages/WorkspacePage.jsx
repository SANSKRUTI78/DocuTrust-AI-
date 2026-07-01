import { useState, useEffect, useRef } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Send, FileText, CheckCircle, Clock, AlertCircle, Shield, ThumbsUp, ThumbsDown, ChevronDown, ChevronUp, Loader, MessageSquare, Plus } from 'lucide-react'
import api from '../utils/api'
import toast from 'react-hot-toast'

function TrustMeter({ score }) {
  const color = score >= 80 ? '#10b981' : score >= 50 ? '#f59e0b' : '#ef4444'
  const label = score >= 80 ? 'High Trust' : score >= 50 ? 'Medium Trust' : 'Low Trust'
  return (
    <div className="flex items-center gap-3">
      <div className="relative w-12 h-12">
        <svg viewBox="0 0 36 36" className="w-12 h-12 -rotate-90">
          <circle cx="18" cy="18" r="15.9" fill="none" stroke="rgba(255,255,255,0.1)" strokeWidth="3" />
          <circle cx="18" cy="18" r="15.9" fill="none" stroke={color} strokeWidth="3"
            strokeDasharray={`${score} 100`} strokeLinecap="round" />
        </svg>
        <span className="absolute inset-0 flex items-center justify-center text-xs font-bold" style={{ color }}>{score}%</span>
      </div>
      <div>
        <p className="text-xs font-medium" style={{ color }}>{label}</p>
        <p className="text-xs text-slate-500">AI Confidence</p>
      </div>
    </div>
  )
}

function AgentLog({ agents }) {
  if (!agents.length) return null
  return (
    <div className="space-y-1.5 p-3 rounded-lg bg-slate-900/80 border border-white/5">
      <p className="text-xs font-medium text-slate-400 mb-2">🤖 Agent Execution</p>
      {agents.map((a, i) => (
        <div key={i} className="flex items-center gap-2 text-xs">
          {a.status === 'running' ? <Loader size={11} className="text-blue-400 animate-spin flex-shrink-0" />
            : <CheckCircle size={11} className="text-emerald-400 flex-shrink-0" />}
          <span className={a.status === 'running' ? 'text-blue-300' : 'text-slate-400'}>
            <span className="text-white font-medium">{a.agent}</span>: {a.message}
          </span>
        </div>
      ))}
    </div>
  )
}

function CitationCard({ citation, index }) {
  const [open, setOpen] = useState(false)
  return (
    <div className="rounded-lg border border-white/10 bg-white/5 overflow-hidden">
      <button onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between p-3 text-left hover:bg-white/5 transition-all">
        <div className="flex items-center gap-2 min-w-0">
          <span className="w-5 h-5 rounded-full bg-blue-600 text-xs flex items-center justify-center text-white font-bold flex-shrink-0">{index + 1}</span>
          <span className="text-xs font-medium text-white truncate">{citation.document_title}</span>
          <span className="text-xs text-slate-400 flex-shrink-0">· Page {citation.page_number}</span>
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          <span className="text-xs text-emerald-400 font-medium">{citation.vector_score}%</span>
          {open ? <ChevronUp size={14} className="text-slate-400" /> : <ChevronDown size={14} className="text-slate-400" />}
        </div>
      </button>
      {open && (
        <div className="px-3 pb-3 border-t border-white/10 pt-3">
          <p className="text-xs text-slate-300 leading-relaxed italic">"{citation.excerpt}..."</p>
        </div>
      )}
    </div>
  )
}

function Message({ msg, onFeedback }) {
  const [showCitations, setShowCitations] = useState(false)
  const [feedbackGiven, setFeedbackGiven] = useState(null)

  const handleFeedback = async (rating) => {
    setFeedbackGiven(rating)
    try {
      await api.post('/chat/feedback', { message_id: msg.id, rating })
      onFeedback?.()
    } catch {}
  }

  if (msg.role === 'user') {
    return (
      <div className="flex justify-end mb-4">
        <div className="max-w-xl bg-blue-600 text-white rounded-2xl rounded-tr-sm px-4 py-3 text-sm">
          {msg.content}
        </div>
      </div>
    )
  }

  return (
    <div className="mb-6">
      {msg.agents && <AgentLog agents={msg.agents} />}
      {msg.content && (
        <div className="mt-3 rounded-xl bg-white/5 border border-white/10 p-4">
          {/* Trust + content header */}
          {msg.trust_score && (
            <div className="flex items-center justify-between mb-4 pb-4 border-b border-white/10">
              <TrustMeter score={msg.trust_score} />
              {msg.reasoning && Object.keys(msg.reasoning).length > 0 && (
                <div className="hidden sm:flex gap-4">
                  {Object.entries(msg.reasoning).map(([k, v]) => (
                    <div key={k} className="text-center">
                      <p className="text-xs font-bold text-blue-400">{v}%</p>
                      <p className="text-xs text-slate-500">{k.replace(/_/g, ' ')}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Answer */}
          <div className="text-sm text-slate-200 leading-relaxed whitespace-pre-wrap">{msg.content}</div>

          {/* Citations */}
          {msg.citations?.length > 0 && (
            <div className="mt-4">
              <button onClick={() => setShowCitations(!showCitations)}
                className="flex items-center gap-2 text-xs text-blue-400 hover:text-blue-300 transition-colors mb-2">
                <FileText size={13} />
                {msg.citations.length} Source{msg.citations.length > 1 ? 's' : ''}
                {showCitations ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
              </button>
              {showCitations && (
                <div className="space-y-2">
                  {msg.citations.map((c, i) => <CitationCard key={i} citation={c} index={i} />)}
                </div>
              )}
            </div>
          )}

          {/* Feedback */}
          {msg.id && (
            <div className="flex items-center gap-2 mt-4 pt-4 border-t border-white/10">
              <span className="text-xs text-slate-500">Was this helpful?</span>
              <button onClick={() => handleFeedback(1)} disabled={feedbackGiven !== null}
                className={`p-1.5 rounded-lg transition-all ${feedbackGiven === 1 ? 'bg-emerald-900/50 text-emerald-400' : 'text-slate-500 hover:text-emerald-400 hover:bg-white/5'}`}>
                <ThumbsUp size={14} />
              </button>
              <button onClick={() => handleFeedback(-1)} disabled={feedbackGiven !== null}
                className={`p-1.5 rounded-lg transition-all ${feedbackGiven === -1 ? 'bg-red-900/50 text-red-400' : 'text-slate-500 hover:text-red-400 hover:bg-white/5'}`}>
                <ThumbsDown size={14} />
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default function WorkspacePage() {
  const [searchParams] = useSearchParams()
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [chatId, setChatId] = useState(searchParams.get('chat') ? parseInt(searchParams.get('chat')) : null)
  const [docs, setDocs] = useState([])
  const [selectedDocs, setSelectedDocs] = useState([])
  const [chatHistory, setChatHistory] = useState([])
  const bottomRef = useRef(null)

  useEffect(() => {
    api.get('/documents/').then(r => setDocs(r.data.filter(d => d.status === 'ready'))).catch(() => {})
    api.get('/chat/history').then(r => setChatHistory(r.data)).catch(() => {})
  }, [])

  useEffect(() => {
    if (chatId) {
      api.get(`/chat/${chatId}/messages`).then(r => {
        setMessages(r.data.map(m => ({ ...m, agents: [] })))
      }).catch(() => {})
    }
  }, [chatId])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const sendMessage = async () => {
    if (!input.trim() || loading) return
    const query = input.trim()
    setInput('')
    setLoading(true)

    setMessages(prev => [...prev, { role: 'user', content: query, id: null, agents: [] }])
    const pendingId = Date.now()
    setMessages(prev => [...prev, { role: 'assistant', content: '', agents: [], trust_score: null, citations: [], id: pendingId }])

    try {
      const res = await fetch('/api/chat/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${JSON.parse(localStorage.getItem('docutrust-auth') || '{}')?.state?.token}`,
        },
        body: JSON.stringify({ query, document_ids: selectedDocs.length ? selectedDocs : null, chat_id: chatId }),
      })

      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let agents = []

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        const text = decoder.decode(value)
        const lines = text.split('\n').filter(l => l.startsWith('data: '))
        for (const line of lines) {
          const raw = line.replace('data: ', '').trim()
          if (raw === '[DONE]') continue
          try {
            const data = JSON.parse(raw)
            if (data.type === 'chat_id') setChatId(data.chat_id)
            else if (data.type === 'message_id') {
              setMessages(prev => prev.map(m => m.id === pendingId ? { ...m, id: data.message_id } : m))
            } else if (data.type === 'result') {
              setMessages(prev => prev.map(m => m.id === pendingId ? {
                ...m, content: data.answer, trust_score: data.trust_score,
                citations: data.citations, reasoning: data.trust_breakdown, agents,
              } : m))
            } else if (data.agent) {
              agents = [...agents.filter(a => a.agent !== data.agent), data]
              setMessages(prev => prev.map(m => m.id === pendingId ? { ...m, agents: [...agents] } : m))
            }
          } catch {}
        }
      }
    } catch (err) {
      toast.error('Failed to get response')
      setMessages(prev => prev.filter(m => m.id !== pendingId))
    } finally {
      setLoading(false)
      api.get('/chat/history').then(r => setChatHistory(r.data)).catch(() => {})
    }
  }

  return (
    <div className="flex h-full">
      {/* Left: Chat history */}
      <div className="w-56 flex-shrink-0 border-r border-white/10 bg-slate-900/50 flex flex-col">
        <div className="p-4 border-b border-white/10">
          <button onClick={() => { setChatId(null); setMessages([]) }}
            className="w-full btn-secondary text-sm justify-center">
            <Plus size={16} /> New Chat
          </button>
        </div>
        <div className="flex-1 overflow-y-auto p-3 space-y-1">
          {chatHistory.map(c => (
            <button key={c.id} onClick={() => setChatId(c.id)}
              className={`w-full text-left px-3 py-2 rounded-lg text-xs transition-all truncate ${c.id === chatId ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white hover:bg-white/5'}`}>
              <MessageSquare size={12} className="inline mr-2" />{c.title}
            </button>
          ))}
        </div>
      </div>

      {/* Main chat */}
      <div className="flex-1 flex flex-col">
        {/* Doc selector */}
        {docs.length > 0 && (
          <div className="px-6 py-3 border-b border-white/10 bg-slate-900/30">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-xs text-slate-400">Search in:</span>
              <button onClick={() => setSelectedDocs([])}
                className={`px-3 py-1 rounded-full text-xs transition-all ${selectedDocs.length === 0 ? 'bg-blue-600 text-white' : 'bg-white/10 text-slate-400 hover:text-white'}`}>
                All Documents
              </button>
              {docs.map(d => (
                <button key={d.id} onClick={() => setSelectedDocs(prev => prev.includes(d.id) ? prev.filter(id => id !== d.id) : [...prev, d.id])}
                  className={`px-3 py-1 rounded-full text-xs transition-all truncate max-w-[160px] ${selectedDocs.includes(d.id) ? 'bg-blue-600 text-white' : 'bg-white/10 text-slate-400 hover:text-white'}`}>
                  {d.title}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-6 py-6">
          {messages.length === 0 && (
            <div className="h-full flex flex-col items-center justify-center text-center">
              <Shield size={48} className="text-slate-700 mb-4" />
              <h2 className="text-xl font-bold text-white mb-2">DocuTrust AI Workspace</h2>
              <p className="text-slate-400 text-sm max-w-md">Ask any question about your uploaded documents. Every answer comes with a Trust Score, citations, and source references.</p>
              {docs.length === 0 && (
                <p className="text-amber-400 text-xs mt-4">⚠ No ready documents found. Upload PDFs first.</p>
              )}
            </div>
          )}
          {messages.map((msg, i) => <Message key={i} msg={msg} />)}
          <div ref={bottomRef} />
        </div>

        {/* Input */}
        <div className="px-6 py-4 border-t border-white/10">
          <div className="flex gap-3">
            <input
              className="input-field flex-1"
              placeholder="Ask anything about your documents..."
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && !e.shiftKey && sendMessage()}
              disabled={loading}
            />
            <button onClick={sendMessage} disabled={loading || !input.trim()} className="btn-primary px-5">
              {loading ? <Loader size={18} className="animate-spin" /> : <Send size={18} />}
            </button>
          </div>
          <p className="text-xs text-slate-600 mt-2 text-center">Answers include Trust Score · Citations · Source Pages</p>
        </div>
      </div>
    </div>
  )
}
