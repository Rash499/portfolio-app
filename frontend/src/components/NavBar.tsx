import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../store/auth'

export default function NavBar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const isActive = (path: string) => location.pathname === path

  return (
    <nav className="sticky top-0 z-50 border-b border-bg-border/80 bg-bg-panel/85 backdrop-blur-xl">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6">
        {/* Brand */}
        <Link
          to="/"
          className="group flex items-center gap-2 font-mono text-sm font-semibold tracking-tight"
        >
          <span className="text-accent transition-colors group-hover:text-accent/80">
            &lt;
          </span>

          <span className="text-slate-100 transition-colors group-hover:text-white">
            ArchPortfolio
          </span>

          <span className="text-accent transition-colors group-hover:text-accent/80">
            /&gt;
          </span>
        </Link>

        {/* Navigation */}
        <div className="flex items-center gap-2 text-sm">
          <Link
            to="/search"
            className={`rounded-md px-3 py-2 transition-all duration-200 ${
              isActive('/search')
                ? 'bg-accent/10 text-accent'
                : 'text-slate-400 hover:bg-white/5 hover:text-slate-100'
            }`}
          >
            Search
          </Link>

          {user ? (
            <>
              <Link
                to="/dashboard"
                className={`rounded-md px-3 py-2 transition-all duration-200 ${
                  isActive('/dashboard')
                    ? 'bg-accent/10 text-accent'
                    : 'text-slate-400 hover:bg-white/5 hover:text-slate-100'
                }`}
              >
                Dashboard
              </Link>

              {/* User */}
              <div className="ml-2 flex items-center gap-3 border-l border-bg-border pl-4">
                <div className="hidden items-center gap-2 sm:flex">
                  <div className="flex h-8 w-8 items-center justify-center rounded-full border border-accent/30 bg-accent/10 font-mono text-xs font-semibold text-accent">
                    {user.username.charAt(0).toUpperCase()}
                  </div>

                  <span className="max-w-32 truncate font-mono text-xs text-slate-300">
                    {user.username}
                  </span>
                </div>

                <button
                  className="rounded-md border border-slate-700 bg-transparent px-3 py-2 text-xs font-medium text-slate-400 transition-all duration-200 hover:border-red-400/40 hover:bg-red-400/5 hover:text-red-400"
                  onClick={() => {
                    logout()
                    navigate('/')
                  }}
                >
                  Logout
                </button>
              </div>
            </>
          ) : (
            <>
              <Link
                to="/login"
                className={`rounded-md px-3 py-2 transition-all duration-200 ${
                  isActive('/login')
                    ? 'bg-accent/10 text-accent'
                    : 'text-slate-400 hover:bg-white/5 hover:text-slate-100'
                }`}
              >
                Login
              </Link>

              <Link
                to="/register"
                className="ml-1 rounded-md border border-accent/50 bg-accent/10 px-4 py-2 font-medium text-accent transition-all duration-200 hover:border-accent hover:bg-accent/20 hover:shadow-[0_0_20px_rgba(0,255,170,0.12)]"
              >
                Get Started
              </Link>
            </>
          )}
        </div>
      </div>
    </nav>
  )
}