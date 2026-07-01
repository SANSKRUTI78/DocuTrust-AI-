import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, FileText, X, CheckCircle, Loader, Tag, Building, Hash } from 'lucide-react'
import api from '../utils/api'
import toast from 'react-hot-toast'

export default function UploadPage() {
  const [files, setFiles] = useState([])
  const [uploading, setUploading] = useState(false)
  const [form, setForm] = useState({ department: '', version: '1.0', tags: '' })

  const onDrop = useCallback((accepted) => {
    const newFiles = accepted.map(f => ({ file: f, status: 'pending', id: Math.random() }))
    setFiles(prev => [...prev, ...newFiles])
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop, accept: { 'application/pdf': ['.pdf'] }, multiple: true
  })

  const removeFile = (id) => setFiles(prev => prev.filter(f => f.id !== id))

  const uploadAll = async () => {
    const pending = files.filter(f => f.status === 'pending')
    if (!pending.length) return toast.error('No files to upload')
    setUploading(true)

    for (const item of pending) {
      setFiles(prev => prev.map(f => f.id === item.id ? { ...f, status: 'uploading' } : f))
      try {
        const fd = new FormData()
        fd.append('file', item.file)
        fd.append('department', form.department)
        fd.append('version', form.version)
        fd.append('tags', JSON.stringify(form.tags.split(',').map(t => t.trim()).filter(Boolean)))
        await api.post('/documents/upload', fd)
        setFiles(prev => prev.map(f => f.id === item.id ? { ...f, status: 'done' } : f))
      } catch (err) {
        setFiles(prev => prev.map(f => f.id === item.id ? { ...f, status: 'error' } : f))
        toast.error(`Failed: ${item.file.name}`)
      }
    }
    setUploading(false)
    toast.success('Upload complete! Processing in background...')
  }

  const statusIcon = (s) => {
    if (s === 'done') return <CheckCircle size={18} className="text-emerald-400" />
    if (s === 'uploading') return <Loader size={18} className="text-blue-400 animate-spin" />
    if (s === 'error') return <X size={18} className="text-red-400" />
    return null
  }

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white">Upload Documents</h1>
        <p className="text-slate-400 mt-1">Upload PDF documents for AI-powered analysis and Q&A</p>
      </div>

      {/* Metadata */}
      <div className="card mb-6">
        <h2 className="text-lg font-semibold text-white mb-4">Document Metadata</h2>
        <div className="grid grid-cols-3 gap-4">
          <div>
            <label className="text-sm text-slate-400 mb-1 flex items-center gap-1"><Building size={14} /> Department</label>
            <input className="input-field" placeholder="e.g. HR, Legal, Finance"
              value={form.department} onChange={e => setForm({ ...form, department: e.target.value })} />
          </div>
          <div>
            <label className="text-sm text-slate-400 mb-1 flex items-center gap-1"><Hash size={14} /> Version</label>
            <input className="input-field" placeholder="1.0"
              value={form.version} onChange={e => setForm({ ...form, version: e.target.value })} />
          </div>
          <div>
            <label className="text-sm text-slate-400 mb-1 flex items-center gap-1"><Tag size={14} /> Tags (comma separated)</label>
            <input className="input-field" placeholder="policy, 2024, travel"
              value={form.tags} onChange={e => setForm({ ...form, tags: e.target.value })} />
          </div>
        </div>
      </div>

      {/* Dropzone */}
      <div {...getRootProps()} className={`border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-all duration-200 ${
        isDragActive ? 'border-blue-500 bg-blue-500/10' : 'border-white/20 hover:border-white/40 bg-white/5'
      }`}>
        <input {...getInputProps()} />
        <Upload size={48} className={`mx-auto mb-4 ${isDragActive ? 'text-blue-400' : 'text-slate-500'}`} />
        <p className="text-lg font-medium text-white mb-1">
          {isDragActive ? 'Drop your PDFs here' : 'Drag & drop PDFs here'}
        </p>
        <p className="text-slate-400 text-sm">or click to browse · Max 50MB per file</p>
      </div>

      {/* File list */}
      {files.length > 0 && (
        <div className="card mt-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-white">{files.length} file{files.length > 1 ? 's' : ''} selected</h2>
            <button onClick={uploadAll} disabled={uploading} className="btn-primary">
              <Upload size={16} /> {uploading ? 'Uploading...' : 'Upload All'}
            </button>
          </div>
          <div className="space-y-3">
            {files.map(item => (
              <div key={item.id} className="flex items-center gap-3 p-3 rounded-lg bg-white/5">
                <FileText size={20} className="text-blue-400 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-white truncate">{item.file.name}</p>
                  <p className="text-xs text-slate-400">{(item.file.size / 1024 / 1024).toFixed(2)} MB</p>
                </div>
                {statusIcon(item.status)}
                {item.status === 'pending' && (
                  <button onClick={() => removeFile(item.id)} className="text-slate-500 hover:text-red-400 transition-colors">
                    <X size={18} />
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Info */}
      <div className="mt-6 p-4 rounded-lg bg-blue-900/30 border border-blue-700/50">
        <h3 className="text-sm font-medium text-blue-300 mb-2">⚡ What happens after upload?</h3>
        <ul className="text-xs text-slate-400 space-y-1">
          <li>• PDF text is extracted using PyMuPDF</li>
          <li>• Text is chunked into semantic segments</li>
          <li>• Embeddings are created using sentence-transformers</li>
          <li>• FAISS vector index is built for fast retrieval</li>
          <li>• Document is marked "Ready" for AI Q&A</li>
        </ul>
      </div>
    </div>
  )
}
