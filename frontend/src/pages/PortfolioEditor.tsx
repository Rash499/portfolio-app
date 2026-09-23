import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import api from '../api/client'
import type { Portfolio, Project } from '../types'

export default function PortfolioEditor() {
  const { portfolioId } = useParams()
  const navigate = useNavigate()
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null)
  const [projects, setProjects] = useState<Project[]>([])
  const [projectName, setProjectName] = useState('')
  const [projectSlug, setProjectSlug] = useState('')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  function load() {
    api.get(`/api/portfolios/${portfolioId}`).then((r) => setPortfolio(r.data))
    api.get(`/api/projects/portfolio/${portfolioId}`).then((r) => setProjects(r.data))
  }
  useEffect(load, [portfolioId])

  async function saveSettings(e: React.FormEvent) {
    e.preventDefault()
    if (!portfolio) return
    setSaving(true)
    try {
      await api.put(`/api/portfolios/${portfolioId}`, {
        title: portfolio.title,
        professional_title: portfolio.professional_title,
        about: portfolio.about,
        skills: portfolio.skills,
        github_url: portfolio.github_url,
        linkedin_url: portfolio.linkedin_url,
        website_url: portfolio.website_url,
        contact_email: portfolio.contact_email,
        is_public: portfolio.is_public,
      })
    } finally {
      setSaving(false)
    }
  }

  async function deletePortfolio() {
    if (!confirm('Delete this portfolio and all its projects?')) return
    await api.delete(`/api/portfolios/${portfolioId}`)
    navigate('/dashboard')
  }

  async function createProject(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    try {
      const { data } = await api.post(`/api/projects/portfolio/${portfolioId}`, {
        name: projectName, slug: projectSlug, technologies: [], key_features: [],
      })
      setProjectName(''); setProjectSlug('')
      navigate(`/dashboard/projects/${data.id}`)
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Could not create project')
    }
  }

  if (!portfolio) return <p className="p-8 text-slate-400">Loading...</p>

  return (
    <div className="max-w-3xl mx-auto py-10 space-y-8">
      <Link to="/dashboard" className="text-sm text-accent">← Back to dashboard</Link>

      <form onSubmit={saveSettings} className="panel p-4 space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="font-medium">Portfolio settings — /{portfolio.slug}</h2>
          {portfolio.is_public && (
            <a className="text-xs text-accent" href={`/p/${portfolio.slug}`} target="_blank" rel="noreferrer">
              View public page →
            </a>
          )}
        </div>
        <div>
          <label className="label">Title</label>
          <input className="input" value={portfolio.title} onChange={(e) => setPortfolio({ ...portfolio, title: e.target.value })} />
        </div>
        <div>
          <label className="label">Professional title</label>
          <input className="input" value={portfolio.professional_title || ''}
                 onChange={(e) => setPortfolio({ ...portfolio, professional_title: e.target.value })} />
        </div>
        <div>
          <label className="label">About</label>
          <textarea className="input" rows={3} value={portfolio.about || ''}
                    onChange={(e) => setPortfolio({ ...portfolio, about: e.target.value })} />
        </div>
        <div>
          <label className="label">Skills (comma separated)</label>
          <input className="input" value={portfolio.skills.join(', ')}
                 onChange={(e) => setPortfolio({ ...portfolio, skills: e.target.value.split(',').map(s => s.trim()).filter(Boolean) })} />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="label">GitHub URL</label>
            <input className="input" value={portfolio.github_url || ''}
                   onChange={(e) => setPortfolio({ ...portfolio, github_url: e.target.value })} />
          </div>
          <div>
            <label className="label">LinkedIn URL</label>
            <input className="input" value={portfolio.linkedin_url || ''}
                   onChange={(e) => setPortfolio({ ...portfolio, linkedin_url: e.target.value })} />
          </div>
        </div>
        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" checked={portfolio.is_public}
                 onChange={(e) => setPortfolio({ ...portfolio, is_public: e.target.checked })} />
          Publish portfolio publicly
        </label>
        <div className="flex gap-2">
          <button className="btn" disabled={saving} type="submit">{saving ? 'Saving...' : 'Save settings'}</button>
          <button className="btn-outline text-red-400" type="button" onClick={deletePortfolio}>Delete portfolio</button>
        </div>
      </form>

      <div>
        <h2 className="font-medium mb-3">Projects</h2>
        <div className="grid gap-3 mb-4">
          {projects.map((p) => (
            <Link key={p.id} to={`/dashboard/projects/${p.id}`} className="panel p-4 flex items-center justify-between hover:border-accent">
              <div>
                <div className="font-medium">{p.name}</div>
                <div className="text-xs text-slate-400">{p.status} · {p.is_published ? 'published' : 'draft'}</div>
              </div>
              <span className="text-accent text-sm">Edit →</span>
            </Link>
          ))}
          {projects.length === 0 && <p className="text-slate-400 text-sm">No projects yet.</p>}
        </div>

        <form onSubmit={createProject} className="panel p-4 space-y-3">
          <h3 className="font-medium text-sm">New project</h3>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">Name</label>
              <input className="input" required value={projectName} onChange={(e) => setProjectName(e.target.value)} />
            </div>
            <div>
              <label className="label">Slug</label>
              <input className="input" required pattern="^[a-z0-9-]+$" value={projectSlug}
                     onChange={(e) => setProjectSlug(e.target.value.toLowerCase())} />
            </div>
          </div>
          {error && <p className="text-red-400 text-sm">{error}</p>}
          <button className="btn" type="submit">Create project</button>
        </form>
      </div>
    </div>
  )
}
