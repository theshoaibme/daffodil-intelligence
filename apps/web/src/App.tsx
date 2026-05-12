import { Routes, Route, Navigate } from 'react-router-dom'
import { ThemeProvider, CssBaseline } from '@mui/material'
import { useAuthStore } from './store'
import { stitchDarkTheme } from './theme/stitch-dark'
import Layout from './components/layout/Layout'
import Home from './pages/home/Home'
import Dashboard from './pages/dashboard/Dashboard'
import Chat from './pages/chat/Chat'
import Agents from './pages/agents/Agents'
import AgentBuilder from './pages/agents/Builder'
import Admin from './pages/admin/Admin'
import Live from './pages/live/Live'
import Vision from './pages/vision/Vision'
import { ErrorBoundary } from './components/ErrorBoundary'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const token = useAuthStore((s) => s.token)
  if (!token) return <Navigate to="/" />
  return <>{children}</>
}

export default function App() {
  return (
    <ErrorBoundary>
      <ThemeProvider theme={stitchDarkTheme}>
        <CssBaseline />
        <Routes>
        <Route path="/" element={<Home />} />
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <Layout><Dashboard /></Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/chat"
          element={
            <ProtectedRoute>
              <Layout><Chat /></Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/agents"
          element={
            <ProtectedRoute>
              <Layout><Agents /></Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/agents/build"
          element={
            <ProtectedRoute>
              <Layout><AgentBuilder /></Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin"
          element={
            <ProtectedRoute>
              <Layout><Admin /></Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/live"
          element={
            <ProtectedRoute>
              <Layout><Live /></Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/vision"
          element={
            <ProtectedRoute>
              <Layout><Vision /></Layout>
            </ProtectedRoute>
          }
        />
      </Routes>
      </ThemeProvider>
    </ErrorBoundary>
  )
}