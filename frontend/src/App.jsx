import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import LoginPage from './pages/LoginPage.jsx'
import DashboardPage from './pages/DashboardPage.jsx'
import AssistantPage from './pages/AssistantPage.jsx'
import ReportsPage from './pages/ReportsPage.jsx'
import TechniquesPage from './pages/TechniquesPage.jsx'
import CvesPage from './pages/CvesPage.jsx'
import { isAuthenticated } from './api/client.js'

function RequireAuth({ children }) {
  if (!isAuthenticated()) {
    return <Navigate to="/login" replace />
  }
  return children
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/" element={<RequireAuth><DashboardPage /></RequireAuth>} />
        <Route path="/assistant" element={<RequireAuth><AssistantPage /></RequireAuth>} />
        <Route path="/reports" element={<RequireAuth><ReportsPage /></RequireAuth>} />
        <Route path="/techniques" element={<RequireAuth><TechniquesPage /></RequireAuth>} />
        <Route path="/cves" element={<RequireAuth><CvesPage /></RequireAuth>} />
      </Routes>
    </BrowserRouter>
  )
}
