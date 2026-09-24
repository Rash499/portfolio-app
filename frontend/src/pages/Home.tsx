import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import axios from 'axios'

type Portfolio = {
  id: number
  name: string
  username?: string
  title?: string
  description?: string
  slug?: string
  technologies?: string[]
}

export default function Home() {
  const [portfolios, setPortfolios] = useState<Portfolio[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const loadPortfolios = async () => {
      try {
        const response = await axios.get('/api/v1/portfolios')
        setPortfolios(response.data)
      } catch (error) {
        console.error('Failed to load portfolios:', error)
      } finally {
        setLoading(false)
      }
    }

    loadPortfolios()
  }, [])

  return (
    <div className="min-h-screen bg-slate-950 text-white">
      {/* Hero */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-indigo-950/50 via-slate-950 to-cyan-950/30" />

        <div className="relative max-w-7xl mx-auto px-6 py-24 lg:py-32">
          <div className="max-w-4xl">
            <div className="inline-flex items-center gap-2 px-4 py-2 mb-6 rounded-full border border-indigo-500/30 bg-indigo-500/10 text-indigo-300 text-sm">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              Interactive Engineering Portfolios
            </div>

            <h1 className="text-5xl md:text-6xl lg:text-7xl font-bold tracking-tight leading-tight">
              Don't just show your
              <span className="block bg-gradient-to-r from-indigo-400 via-cyan-400 to-emerald-400 bg-clip-text text-transparent">
                experience. Show the system.
              </span>
            </h1>

            <p className="mt-7 max-w-2xl text-lg md:text-xl leading-8 text-slate-400">
              Explore real architectures built by DevOps, cloud, SRE,
              platform, security, and infrastructure engineers.
              Click through services, databases, Kubernetes clusters,
              CI/CD pipelines, security controls, and observability.
            </p>

            <div className="flex flex-wrap gap-4 mt-9">
              <Link
                to="/register"
                className="px-6 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-500
                           font-semibold transition-all shadow-lg shadow-indigo-600/20"
              >
                Create your portfolio
              </Link>

              <Link
                to="/search"
                className="px-6 py-3 rounded-xl border border-slate-700
                           bg-slate-900/70 hover:bg-slate-800
                           font-semibold transition-all"
              >
                Explore portfolios →
              </Link>
            </div>
          </div>

          {/* Feature cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5 mt-20">
            <FeatureCard
              icon="◈"
              title="Interactive Architecture"
              description="Let visitors explore your infrastructure node by node."
            />

            <FeatureCard
              icon="⌘"
              title="DevOps Workflows"
              description="Show CI/CD, GitOps, containers, Kubernetes and deployments."
            />

            <FeatureCard
              icon="◉"
              title="Real Engineering"
              description="Turn your projects and technical experience into something people can explore."
            />
          </div>
        </div>
      </section>

      {/* Portfolio section */}
      <section className="max-w-7xl mx-auto px-6 py-20">
        <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-5 mb-10">
          <div>
            <p className="text-sm font-semibold uppercase tracking-widest text-indigo-400 mb-2">
              Discover
            </p>

            <h2 className="text-3xl md:text-4xl font-bold">
              Available portfolios
            </h2>

            <p className="text-slate-400 mt-3 max-w-2xl">
              Explore engineers, architectures, projects and infrastructure
              through interactive portfolios.
            </p>
          </div>

          <Link
            to="/search"
            className="text-indigo-400 hover:text-indigo-300 font-medium"
          >
            View all portfolios →
          </Link>
        </div>

        {loading ? (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[1, 2, 3].map((item) => (
              <div
                key={item}
                className="h-64 rounded-2xl bg-slate-900 border border-slate-800 animate-pulse"
              />
            ))}
          </div>
        ) : portfolios.length === 0 ? (
          <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-12 text-center">
            <div className="text-4xl mb-4">◇</div>

            <h3 className="text-xl font-semibold">
              No portfolios yet
            </h3>

            <p className="text-slate-400 mt-2 mb-6">
              Be one of the first engineers to create an interactive portfolio.
            </p>

            <Link
              to="/register"
              className="inline-flex px-5 py-3 rounded-xl bg-indigo-600
                         hover:bg-indigo-500 font-semibold transition"
            >
              Create the first portfolio
            </Link>
          </div>
        ) : (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {portfolios.map((portfolio) => (
              <PortfolioCard
                key={portfolio.id}
                portfolio={portfolio}
              />
            ))}
          </div>
        )}
      </section>

      {/* Bottom CTA */}
      <section className="max-w-7xl mx-auto px-6 pb-20">
        <div className="relative overflow-hidden rounded-3xl border border-indigo-500/20 bg-gradient-to-r from-indigo-950/70 to-slate-900 p-10 md:p-14">
          <div className="absolute -right-20 -top-20 w-64 h-64 bg-indigo-500/10 rounded-full blur-3xl" />

          <div className="relative max-w-2xl">
            <p className="text-indigo-400 font-semibold mb-3">
              Build something worth exploring
            </p>

            <h2 className="text-3xl md:text-4xl font-bold">
              Turn your engineering journey into an interactive experience.
            </h2>

            <p className="text-slate-400 mt-4 leading-7">
              Showcase your projects, infrastructure, technologies,
              architecture decisions and DevOps workflows in one place.
            </p>

            <Link
              to="/register"
              className="inline-flex mt-7 px-6 py-3 rounded-xl bg-white
                         text-slate-950 hover:bg-slate-200 font-semibold transition"
            >
              Create your portfolio
            </Link>
          </div>
        </div>
      </section>
    </div>
  )
}

function FeatureCard({
  icon,
  title,
  description,
}: {
  icon: string
  title: string
  description: string
}) {
  return (
    <div className="group rounded-2xl border border-slate-800 bg-slate-900/70
                    p-6 hover:border-indigo-500/40 hover:bg-slate-900
                    transition-all">
      <div className="flex items-center justify-center w-11 h-11 rounded-xl
                      bg-indigo-500/10 text-indigo-400 text-xl mb-5
                      group-hover:bg-indigo-500/20 transition">
        {icon}
      </div>

      <h3 className="text-lg font-semibold mb-2">
        {title}
      </h3>

      <p className="text-sm leading-6 text-slate-400">
        {description}
      </p>
    </div>
  )
}

function PortfolioCard({
  portfolio,
}: {
  portfolio: Portfolio
}) {
  const portfolioUrl = portfolio.slug
    ? `/portfolio/${portfolio.slug}`
    : `/portfolio/${portfolio.id}`

  return (
    <Link
      to={portfolioUrl}
      className="group block rounded-2xl border border-slate-800
                 bg-slate-900/70 p-6 hover:-translate-y-1
                 hover:border-indigo-500/40 hover:bg-slate-900
                 transition-all duration-200"
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-center justify-center w-12 h-12 rounded-xl
                        bg-gradient-to-br from-indigo-500/20 to-cyan-500/20
                        border border-indigo-500/20 text-indigo-300
                        font-bold text-lg">
          {(portfolio.name || 'P').charAt(0).toUpperCase()}
        </div>

        <span className="text-slate-600 group-hover:text-indigo-400 transition">
          ↗
        </span>
      </div>

      <h3 className="text-xl font-semibold mt-5 group-hover:text-indigo-300 transition">
        {portfolio.name}
      </h3>

      {portfolio.username && (
        <p className="text-sm text-indigo-400 mt-1">
          @{portfolio.username}
        </p>
      )}

      {portfolio.title && (
        <p className="text-sm text-slate-300 mt-4">
          {portfolio.title}
        </p>
      )}

      {portfolio.description && (
        <p className="text-sm text-slate-500 leading-6 mt-3 line-clamp-3">
          {portfolio.description}
        </p>
      )}

      {portfolio.technologies &&
        portfolio.technologies.length > 0 && (
          <div className="flex flex-wrap gap-2 mt-5">
            {portfolio.technologies.slice(0, 4).map((technology) => (
              <span
                key={technology}
                className="px-2.5 py-1 rounded-lg bg-slate-800
                           text-xs text-slate-400 border border-slate-700"
              >
                {technology}
              </span>
            ))}
          </div>
        )}

      <div className="mt-6 pt-4 border-t border-slate-800">
        <span className="text-sm font-medium text-indigo-400
                         group-hover:text-indigo-300">
          Explore architecture →
        </span>
      </div>
    </Link>
  )
}
