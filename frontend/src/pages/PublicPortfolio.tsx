import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import api from '../api/client'
import type { Portfolio, Project } from '../types'

export default function PublicPortfolio() {
  const { slug } = useParams()
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null)
  const [projects, setProjects] = useState<Project[]>([])
  const [notFound, setNotFound] = useState(false)

  useEffect(() => {
    api.get(`/api/portfolios/public/${slug}`)
      .then((r) => setPortfolio(r.data))
      .catch(() => setNotFound(true))
    api.get(`/api/portfolios/public/${slug}/projects`).then((r) => setProjects(r.data))
  }, [slug])

  if (notFound) return <p className="p-8 text-slate-400">Portfolio not found or not public.</p>
  if (!portfolio) return <p className="p-8 text-slate-400">Loading...</p>

  return (
    <div className="max-w-4xl mx-auto py-12 space-y-10">
      <header>
        <h1 className="text-3xl font-bold">{portfolio.title}</h1>
        {portfolio.professional_title && <p className="text-accent mt-1">{portfolio.professional_title}</p>}
        {portfolio.about && <p className="text-slate-300 mt-4 max-w-2xl">{portfolio.about}</p>}
        {portfolio.skills.length > 0 && (
          <div className="flex flex-wrap gap-2 mt-4">
            {portfolio.skills.map((s) => (
              <span key={s} className="text-xs px-2 py-1 rounded-full border border-bg-border text-slate-300">{s}</span>
            ))}
          </div>
        )}
        <div className="flex gap-4 mt-4 text-sm">
          {portfolio.github_url && <a className="text-accent" href={portfolio.github_url} target="_blank" rel="noreferrer">GitHub</a>}
          {portfolio.linkedin_url && <a className="text-accent" href={portfolio.linkedin_url} target="_blank" rel="noreferrer">LinkedIn</a>}
          {portfolio.website_url && <a className="text-accent" href={portfolio.website_url} target="_blank" rel="noreferrer">Website</a>}
        </div>
      </header>

      <section>
        <h2 className="text-xl font-semibold mb-4">Projects</h2>
        <div className="grid gap-4">
          {projects.map((p) => (
            <Link key={p.id} to={`/p/${slug}/${p.slug}`} className="panel p-5 block hover:border-accent">
              <div className="flex items-center justify-between">
                <h3 className="font-medium">{p.name}</h3>
                <span className="text-xs px-2 py-0.5 rounded-full border border-bg-border">{p.status}</span>
              </div>
              {p.short_description && <p className="text-sm text-slate-400 mt-2">{p.short_description}</p>}
              <div className="flex flex-wrap gap-1 mt-3">
                {p.technologies.map((t) => (
                  <span key={t} className="text-[10px] px-2 py-0.5 rounded bg-bg-border text-slate-300">{t}</span>
                ))}
              </div>
              <span className="text-accent text-sm mt-3 inline-block">Explore interactive architecture →</span>
            </Link>
          ))}
          {projects.length === 0 && <p className="text-slate-400 text-sm">No published projects yet.</p>}
        </div>
      </section>
    </div>
  )
}
