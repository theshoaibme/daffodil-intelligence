import { useState } from 'react'
import { Box, Container, Typography, Button, TextField, Card, CardContent, Grid, Alert } from '@mui/material'
import { Rocket, Psychology, Videocam, Speed } from '@mui/icons-material'
import { useNavigate } from 'react-router-dom'
import { api } from '../../services/api'
import { useAuthStore } from '../../store'

export default function Home() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [isRegister, setIsRegister] = useState(false)
  const [error, setError] = useState('')
  const navigate = useNavigate()
  const { setToken } = useAuthStore()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    try {
      if (isRegister) {
        await api.register({ email, password, full_name: email.split('@')[0] })
      }
      await api.login(email, password)
      setToken('logged_in')
      navigate('/dashboard')
    } catch (err) {
      setError('Authentication failed')
    }
  }

  const features = [
    { icon: <Psychology fontSize="large" />, title: '12 AI Agents', desc: 'Academic, Library, Career, Coding & more' },
    { icon: <Videocam fontSize="large" />, title: 'Live Voice', desc: 'Real-time Gemini voice conversations' },
    { icon: <Speed fontSize="large" />, title: 'RAG System', desc: 'Instant knowledge retrieval' },
    { icon: <Rocket fontSize="large" />, title: 'Multi-Channel', desc: 'Web, WhatsApp, Telegram, Discord' },
  ]

  return (
    <Box sx={{ minHeight: '100vh', bgcolor: '#0f172a', color: 'white' }}>
      <Box sx={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, background: 'radial-gradient(circle at 30% 50%, rgba(99,102,241,0.15) 0%, transparent 50%), radial-gradient(circle at 70% 80%, rgba(236,72,153,0.1) 0%, transparent 40%)', pointerEvents: 'none' }} />

      <Container maxWidth="lg" sx={{ position: 'relative', pt: 15, pb: 10 }}>
        <Box sx={{ textAlign: 'center', mb: 8 }}>
          <Typography variant="h2" sx={{ fontWeight: 800, mb: 2, background: 'linear-gradient(135deg, #6366f1, #ec4899)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
            Daffodil Intelligence
          </Typography>
          <Typography variant="h5" sx={{ color: '#94a3b8', mb: 4 }}>
            360° Multi-Agent AI Operating System for University
          </Typography>
          <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center' }}>
            <Button variant="contained" size="large" sx={{ bgcolor: '#6366f1', px: 4 }} onClick={() => setIsRegister(false)}>Get Started</Button>
            <Button variant="outlined" size="large" sx={{ color: 'white', borderColor: '#6366f1' }}>Learn More</Button>
          </Box>
        </Box>

        <Grid container spacing={3} sx={{ mb: 8 }}>
          {features.map((f, i) => (
            <Grid item xs={12} sm={6} md={3} key={i}>
              <Card sx={{ bgcolor: 'rgba(30,41,59,0.8)', border: '1px solid #334155', height: '100%' }}>
                <CardContent sx={{ textAlign: 'center', p: 3 }}>
                  <Box sx={{ color: '#6366f1', mb: 2 }}>{f.icon}</Box>
                  <Typography variant="h6" sx={{ mb: 1 }}>{f.title}</Typography>
                  <Typography variant="body2" sx={{ color: '#94a3b8' }}>{f.desc}</Typography>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>

        <Box sx={{ maxWidth: 400, mx: 'auto' }}>
          <Card sx={{ bgcolor: 'rgba(30,41,59,0.8)', border: '1px solid #334155', p: 3 }}>
            <Typography variant="h5" sx={{ mb: 3, textAlign: 'center' }}>{isRegister ? 'Create Account' : 'Login'}</Typography>
            {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
            <form onSubmit={handleSubmit}>
              <TextField fullWidth label="Email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} sx={{ mb: 2 }} />
              <TextField fullWidth label="Password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} sx={{ mb: 2 }} />
              <Button fullWidth variant="contained" type="submit" sx={{ bgcolor: '#6366f1', py: 1.5 }}>{isRegister ? 'Register' : 'Login'}</Button>
            </form>
            <Button fullWidth sx={{ mt: 2 }} onClick={() => setIsRegister(!isRegister)}>
              {isRegister ? 'Already have account? Login' : "Don't have account? Register"}
            </Button>
          </Card>
        </Box>
      </Container>
    </Box>
  )
}