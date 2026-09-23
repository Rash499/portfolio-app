import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import api from '../api/client'
import type { ApiEndpoint, Project } from '../types'

const METHODS = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']

export default function ProjectEditor() {
  const { projectId } = useParams()
  const navigate = useNavigate()
  const [project, setProject] = useState<Project | null>(null)
  const [endpoints, setEndpoints] = useState<ApiEndpoint[]>([])
  const [saving, setSaving] = useState(false)

  const [method, setMethod] = useState('GET')
  const [path, setPath] = useState('')
  const [desc, setDesc] = useState('')

  function load() {
    api.get(`/api/projects/${projectId}`).then((r) => setProject(r.data))
    api.get(`/api/projects/${projectId}/endpoints`).then((r) => setEndpoints(r.data))
  }
  useEffect(load, [projectId])

  async function save(e: React.FormEvent) {
    e.preventDefault()
    if (!project) return
    setSaving(true)
    try {
      await api.put(`/api/projects/${projectId}`, {
        name: project.name,
        short_description: project.short_description,
        full_description: project.full_description,
        status: project.status,
        technologies: project.technologies,
        github_url: project.github_url,
        live_url: project.live_url,
        is_published: project.is_published,
      })
    } finally {
      setSaving(false)
    }
  }

  async function deleteProject() {
    if (!confirm('Delete this project?')) return
    await api.delete(`/api/projects/${projectId}`)
    navigate(`/dashboard/portfolios/${project?.portfolio_id}`)
  }

  async function addEndpoint(e: React.FormEvent) {
    e.preventDefault()
    await api.post(`/api/projects/${projectId}/endpoints`, {
      method, path, description: desc, requires_auth: false, status_codes: [200],
    })
    setPath(''); setDesc('')
    load()
  }

  async function removeEndpoint(id: string) {
    await api.delete(`/api/endpoints/${id}`)
    load()
  }

  if (!project) return <p className="p-8 text-slate-400">Loading...</p>

  return (
    <div className="max-w-3xl mx-auto py-10 space-y-8">
      <Link to={`/dashboard/portfolios/${project.portfolio_id}`} className="text-sm text-accent">← Back to portfolio</Link>

      <form onSubmit={save} className="panel p-4 space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="font-medium">Project settings</h2>
          <Link className="btn" to={`/dashboard/projects/${projectId}/architecture`}>Open architecture editor →</Link>
        </div>
        <div>
          <label className="label">Name</label>
          <input className="input" value={project.name} onChange={(e) => setProject({ ...project, name: e.target.value })} />
        </div>
        <div>
          <label className="label">Short description</label>
          <input className="input" value={project.short_description || ''}
                 onChange={(e) => setProject({ ...project, short_description: e.target.value })} />
        </div>
        <div>
          <label className="label">Full description</label>
          <textarea className="input" rows={4} value={project.full_description || ''}
                    onChange={(e) => setProject({ ...project, full_description: e.target.value })} />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="label">Status</label>
            <select className="input" value={project.status} onChange={(e) => setProject({ ...project, status: e.target.value })}>
              {['planning', 'development', 'completed', 'maintenance', 'archived'].map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="label">Technologies (comma separated)</label>
            <input className="input" value={project.technologies.join(', ')}
                   onChange={(e) => setProject({ ...project, technologies: e.target.value.split(',').map(s => s.trim()).filter(Boolean) })} />
          </div>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="label">GitHub URL</label>
            <input className="input" value={project.github_url || ''} onChange={(e) => setProject({ ...project, github_url: e.target.value })} />
          </div>
          <div>
            <label className="label">Live URL</label>
            <input className="input" value={project.live_url || ''} onChange={(e) => setProject({ ...project, live_url: e.target.value })} />
          </div>
        </div>
        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" checked={project.is_published}
                 onChange={(e) => setProject({ ...project, is_published: e.target.checked })} />
          Published (visible on public portfolio)
        </label>
        <div className="flex gap-2">
          <button className="btn" disabled={saving} type="submit">{saving ? 'Saving...' : 'Save'}</button>
          <button className="btn-outline text-red-400" type="button" onClick={deleteProject}>Delete project</button>
        </div>
      </form>

      <div className="panel p-4 space-y-3">
        <h2 className="font-medium">API Explorer</h2>
        <div className="space-y-2">
          {endpoints.map((ep) => (
            <div key={ep.id} className="flex items-center justify-between text-sm border-b border-bg-border pb-2">
              <div>
                <span className="font-mono text-accent mr-2">{ep.method}</span>
                <span className="font-mono">{ep.path}</span>
                {ep.description && <span className="text-slate-400 ml-2">— {ep.description}</span>}
              </div>
              <button className="text-red-400 text-xs" onClick={() => removeEndpoint(ep.id)}>remove</button>
            </div>
          ))}
          {endpoints.length === 0 && <p className="text-slate-400 text-sm">No endpoints documented yet.</p>}
        </div>
        <form onSubmit={addEndpoint} className="grid grid-cols-[100px_1fr_1fr_auto] gap-2 items-end pt-2">
          <div>
            <label className="label">Method</label>
            <select className="input" value={method} onChange={(e) => setMethod(e.target.value)}>
              {METHODS.map((m) => <option key={m} value={m}>{m}</option>)}
            </select>
          </div>
          <div>
            <label className="label">Path</label>
            <input className="input" required value={path} onChange={(e) => setPath(e.target.value)} placeholder="/api/projects/{id}" />
          </div>
          <div>
            <label className="label">Description</label>
            <input className="input" value={desc} onChange={(e) => setDesc(e.target.value)} />
          </div>
          <button className="btn" type="submit">Add</button>
        </form>
      </div>
    </div>
  )
}
