import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../api/client'
import type { Portfolio } from '../types'

export default function Dashboard() {
  const [portfolios, setPortfolios] = useState<Portfolio[]>([])
  const [slug, setSlug] = useState('')
  const [title, setTitle] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  function load() {
    api.get('/api/portfolios/me').then((r) => setPortfolios(r.data)).finally(() => setLoading(false))
  }

  useEffect(load, [])

  async function createPortfolio(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    try {
      await api.post('/api/portfolios', { slug, title, skills: [] })
      setSlug(''); setTitle('')
      load()
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Could not create portfolio')
    }
  }

  return (
    <div className="max-w-3xl mx-auto py-10 space-y-8">
      <div>
        <h1 className="text-2xl font-semibold mb-1">Your portfolios</h1>
        <p className="text-slate-400 text-sm">Each portfolio can hold multiple interactive-architecture projects.</p>
      </div>

      {loading ? (
        <p className="text-slate-400">Loading...</p>
      ) : portfolios.length === 0 ? (
        <p className="text-slate-400">No portfolios yet — create your first one below.</p>
      ) : (
        <div className="grid gap-3">
          {portfolios.map((p) => (
            <Link key={p.id} to={`/dashboard/portfolios/${p.id}`} className="panel p-4 flex items-center justify-between hover:border-accent">
              <div>
                <div className="font-medium">{p.title}</div>
                <div className="text-xs text-slate-400">/{p.slug} · {p.is_public ? 'public' : 'private'}</div>
              </div>
              <span className="text-accent text-sm">Manage →</span>
            </Link>
          ))}
        </div>
      )}

      <form onSubmit={createPortfolio} className="panel p-4 space-y-3">
        <h2 className="font-medium">Create a new portfolio</h2>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="label">Title</label>
            <input className="input" required value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Rashmika Dilmin" />
          </div>
          <div>
            <label className="label">Slug (URL)</label>
            <input className="input" required pattern="^[a-z0-9-]+$" value={slug}
                   onChange={(e) => setSlug(e.target.value.toLowerCase())} placeholder="rashmika-dilmin" />
          </div>
        </div>
        {error && <p className="text-red-400 text-sm">{error}</p>}
        <button className="btn" type="submit">Create portfolio</button>
      </form>
    </div>
  )
}
