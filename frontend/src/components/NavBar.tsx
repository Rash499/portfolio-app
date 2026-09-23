import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../store/auth'

export default function NavBar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  return (
    <nav className="border-b border-bg-border bg-bg-panel/60 backdrop-blur px-6 py-3 flex items-center justify-between">
      <Link to="/" className="font-mono text-accent font-semibold">
        &lt;ArchPortfolio/&gt;
      </Link>
      <div className="flex items-center gap-4 text-sm">
        <Link to="/search" className="text-slate-300 hover:text-accent">Search</Link>
        {user ? (
          <>
            <Link to="/dashboard" className="text-slate-300 hover:text-accent">Dashboard</Link>
            <button
              className="btn-outline"
              onClick={() => { logout(); navigate('/') }}
            >
              Logout ({user.username})
            </button>
          </>
        ) : (
          <>
            <Link to="/login" className="text-slate-300 hover:text-accent">Login</Link>
            <Link to="/register" className="btn">Get Started</Link>
          </>
        )}
      </div>
    </nav>
  )
}
