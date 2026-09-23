import { Link } from 'react-router-dom'

export default function Home() {
  return (
    <div className="max-w-3xl mx-auto py-20 text-center">
      <h1 className="text-4xl font-bold mb-4">
        Build a portfolio people can <span className="text-accent">click through</span>, not just read.
      </h1>
      <p className="text-slate-400 max-w-xl mx-auto mb-8">
        For DevOps, cloud, SRE, and platform engineers. Model your real system
        architecture — services, databases, Kubernetes, CI/CD, GitOps, security,
        observability — as an interactive diagram visitors can explore node by node.
      </p>
      <div className="flex gap-3 justify-center">
        <Link to="/register" className="btn">Create your portfolio</Link>
        <Link to="/search" className="btn-outline">Browse portfolios</Link>
      </div>
    </div>
  )
}
