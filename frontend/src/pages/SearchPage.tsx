import { useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../api/client'

interface Result {
  type: string
  label: string
  portfolio_slug: string
  project_slug?: string
}

export default function SearchPage() {
  const [q, setQ] = useState('')
  const [results, setResults] = useState<Result[]>([])
  const [searched, setSearched] = useState(false)

  async function runSearch(e: React.FormEvent) {
    e.preventDefault()
    if (!q.trim()) return
    const { data } = await api.get('/api/search', { params: { q } })
    setResults(data)
    setSearched(true)
  }

  function linkFor(r: Result) {
    return r.project_slug ? `/p/${r.portfolio_slug}/${r.project_slug}` : `/p/${r.portfolio_slug}`
  }

  return (
    <div className="max-w-2xl mx-auto py-12">
      <h1 className="text-2xl font-semibold mb-4">Search portfolios &amp; projects</h1>
      <form onSubmit={runSearch} className="flex gap-2 mb-6">
        <input className="input" placeholder="Kubernetes, FastAPI, Argo CD..." value={q} onChange={(e) => setQ(e.target.value)} />
        <button className="btn" type="submit">Search</button>
      </form>

      <div className="space-y-2">
        {results.map((r, i) => (
          <Link key={i} to={linkFor(r)} className="panel p-3 flex items-center justify-between hover:border-accent">
            <span>{r.label}</span>
            <span className="text-xs text-slate-400 uppercase">{r.type.replace(/_/g, ' ')}</span>
          </Link>
        ))}
        {searched && results.length === 0 && <p className="text-slate-400 text-sm">No results.</p>}
      </div>
    </div>
  )
}
