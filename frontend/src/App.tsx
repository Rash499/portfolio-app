import { useEffect } from 'react'
import { Routes, Route } from 'react-router-dom'
import NavBar from './components/NavBar'
import ProtectedRoute from './components/ProtectedRoute'
import { useAuth } from './store/auth'

import Home from './pages/Home'
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import PortfolioEditor from './pages/PortfolioEditor'
import ProjectEditor from './pages/ProjectEditor'
import ArchitectureEditor from './pages/ArchitectureEditor'
import PublicPortfolio from './pages/PublicPortfolio'
import PublicProject from './pages/PublicProject'
import SearchPage from './pages/SearchPage'

export default function App() {
  const fetchMe = useAuth((s) => s.fetchMe)
  useEffect(() => { fetchMe() }, [fetchMe])

  return (
    <div className="min-h-screen">
      <NavBar />
      <main className="px-4">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/search" element={<SearchPage />} />
          <Route path="/p/:slug" element={<PublicPortfolio />} />
          <Route path="/p/:slug/:projectSlug" element={<PublicProject />} />

          <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
          <Route path="/dashboard/portfolios/:portfolioId" element={<ProtectedRoute><PortfolioEditor /></ProtectedRoute>} />
          <Route path="/dashboard/projects/:projectId" element={<ProtectedRoute><ProjectEditor /></ProtectedRoute>} />
          <Route path="/dashboard/projects/:projectId/architecture" element={<ProtectedRoute><ArchitectureEditor /></ProtectedRoute>} />
        </Routes>
      </main>
    </div>
  )
}
