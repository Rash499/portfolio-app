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

    const { data } = await api.get('/api/search', {
      params: { q },
    })

    setResults(data)
    setSearched(true)
  }

  function linkFor(r: Result) {
    return r.project_slug
      ? `/p/${r.portfolio_slug}/${r.project_slug}`
      : `/p/${r.portfolio_slug}`
  }

  return (
    <div className="min-h-[calc(100vh-5rem)] px-4 py-12">
      <div className="mx-auto w-full max-w-3xl">

        {/* Header */}
        <div className="mb-8 text-center">
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl border border-accent/30 bg-accent/10">
            <svg
              className="h-7 w-7 text-accent"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <circle cx="11" cy="11" r="7" />
              <path d="m20 20-4-4" />
            </svg>
          </div>

          <h1 className="text-3xl font-bold tracking-tight text-white">
            Search portfolios &amp; projects
          </h1>

          <p className="mx-auto mt-2 max-w-xl text-sm text-slate-400">
            Find portfolios and projects by technology, framework, tool, or
            project name.
          </p>
        </div>

        {/* Search Form */}
        <form
          onSubmit={runSearch}
          className="panel mb-8 flex flex-col gap-3 p-3 sm:flex-row"
        >
          <div className="relative flex-1">
            <svg
              className="pointer-events-none absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-slate-500"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <circle cx="11" cy="11" r="7" />
              <path d="m20 20-4-4" />
            </svg>

            <input
              className="input w-full pl-10 focus:ring-2 focus:ring-accent/40"
              placeholder="Kubernetes, FastAPI, Argo CD..."
              value={q}
              onChange={(e) => setQ(e.target.value)}
            />
          </div>

          <button
            className="btn min-w-[110px] transition hover:scale-[1.01] disabled:cursor-not-allowed disabled:opacity-50"
            type="submit"
            disabled={!q.trim()}
          >
            Search
          </button>
        </form>

        {/* Results Header */}
        {searched && results.length > 0 && (
          <div className="mb-3 flex items-center justify-between">
            <p className="text-sm font-medium text-slate-300">
              Search results
            </p>

            <span className="rounded-full border border-slate-700 bg-slate-800/60 px-3 py-1 text-xs text-slate-400">
              {results.length} {results.length === 1 ? 'result' : 'results'}
            </span>
          </div>
        )}

        {/* Results */}
        <div className="space-y-3">
          {results.map((r, i) => (
            <Link
              key={i}
              to={linkFor(r)}
              className="group flex items-center justify-between gap-4 rounded-xl border border-slate-700/60 bg-slate-900/50 p-4 transition duration-200 hover:-translate-y-0.5 hover:border-accent/50 hover:bg-slate-800/70 hover:shadow-lg"
            >
              <div className="flex min-w-0 items-center gap-4">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border border-slate-700 bg-slate-800 text-slate-400 transition group-hover:border-accent/30 group-hover:text-accent">
                  {r.project_slug ? (
                    <svg
                      className="h-5 w-5"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    >
                      <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
                      <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
                    </svg>
                  ) : (
                    <svg
                      className="h-5 w-5"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    >
                      <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
                      <circle cx="9" cy="7" r="4" />
                      <path d="M22 21v-2a4 4 0 0 0-3-3.87" />
                      <path d="M16 3.13a4 4 0 0 1 0 7.75" />
                    </svg>
                  )}
                </div>

                <div className="min-w-0">
                  <p className="truncate font-medium text-slate-100 transition group-hover:text-accent">
                    {r.label}
                  </p>

                  <p className="mt-1 truncate text-xs text-slate-500">
                    {r.project_slug
                      ? `Project · ${r.portfolio_slug}`
                      : `Portfolio · ${r.portfolio_slug}`}
                  </p>
                </div>
              </div>

              <div className="flex shrink-0 items-center gap-3">
                <span className="hidden rounded-full border border-slate-700 bg-slate-800/60 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wider text-slate-400 sm:inline-block">
                  {r.type.replace(/_/g, ' ')}
                </span>

                <svg
                  className="h-5 w-5 text-slate-600 transition group-hover:translate-x-1 group-hover:text-accent"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <path d="M5 12h14" />
                  <path d="m12 5 7 7-7 7" />
                </svg>
              </div>
            </Link>
          ))}

          {/* Empty State */}
          {searched && results.length === 0 && (
            <div className="panel flex flex-col items-center px-6 py-12 text-center">
              <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-slate-800 text-slate-500">
                <svg
                  className="h-6 w-6"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <circle cx="11" cy="11" r="7" />
                  <path d="m20 20-4-4" />
                </svg>
              </div>

              <h2 className="font-medium text-slate-200">
                No results found
              </h2>

              <p className="mt-1 max-w-sm text-sm text-slate-500">
                We couldn't find anything matching{' '}
                <span className="text-slate-300">"{q}"</span>. Try another
                technology, project, or portfolio name.
              </p>
            </div>
          )}

          {/* Initial State */}
          {!searched && (
            <div className="mt-8 text-center">
              <p className="text-sm text-slate-500">
                Try searching for{' '}
                <span className="text-slate-400">Kubernetes</span>,{' '}
                <span className="text-slate-400">FastAPI</span>,{' '}
                <span className="text-slate-400">React</span>, or{' '}
                <span className="text-slate-400">Argo CD</span>.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}