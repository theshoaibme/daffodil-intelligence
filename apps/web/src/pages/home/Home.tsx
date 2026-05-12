import { useState, useEffect } from 'react'
import { Box, Typography, Button, TextField, InputAdornment, CircularProgress, IconButton } from '@mui/material'
import { Visibility, VisibilityOff, Google, GitHub } from '@mui/icons-material'
import { useNavigate } from 'react-router-dom'
import { api } from '../../services/api'
import { useAuthStore } from '../../store'

interface User {
  id?: number;
  email?: string;
  full_name?: string;
  role?: string;
  student_id?: string;
  department?: string;
  semester?: number;
  cgpa?: number;
}

const colors = {
  surface: '#131314',
  surfaceContainer: '#201f20',
  surfaceContainerHigh: '#2a2a2b',
  surfaceContainerHighest: '#353436',
  onSurface: '#e5e2e3',
  onSurfaceVariant: '#c3c6d1',
  outline: '#8d919b',
  primary: '#8ab4f8',
  primaryContainer: '#8ab4f8',
  secondary: '#c5c7c5',
}

export default function Home() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [name, setName] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [isRegister, setIsRegister] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  const [success, setSuccess] = useState('')
  const navigate = useNavigate()
  const { setUser } = useAuthStore()

  useEffect(() => {
    const token = localStorage.getItem('di_token')
    if (token) {
      navigate('/dashboard')
    }
  }, [navigate])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setSuccess('')
    setLoading(true)

    if (isRegister) {
      if (!name.trim()) {
        setError('Please enter your name')
        setLoading(false)
        return
      }
      if (password !== confirmPassword) {
        setError('Passwords do not match')
        setLoading(false)
        return
      }
      if (password.length < 6) {
        setError('Password must be at least 6 characters')
        setLoading(false)
        return
      }
    }

    try {
      if (isRegister) {
        const data = await api.register(name, email, password) as { user?: User }
        if (data.user) {
          setUser(data.user)
        }
        setSuccess('Account created successfully! Redirecting...')
        setTimeout(() => navigate('/dashboard'), 1500)
      } else {
        const data = await api.login(email, password) as { user?: User }
        if (data.user) {
          setUser(data.user)
        }
        navigate('/dashboard')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Authentication failed. Please try again.')
    }

    setLoading(false)
  }

  return (
    <Box sx={{ 
      minHeight: '100vh', 
      bgcolor: colors.surface, 
      color: colors.onSurface,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      p: { xs: 2, md: 4 }
    }}>
      <Box sx={{ 
        width: '100%', 
        maxWidth: 480,
        bgcolor: '#191A1F',
        borderRadius: '48px',
        border: '1px solid #444746',
        p: { xs: 3, md: 5 }
      }}>
        <Box sx={{ textAlign: 'center', mb: 4 }}>
          <Typography sx={{ 
            fontSize: { xs: '28px', md: '32px' },
            fontWeight: 500,
            color: colors.onSurface,
            mb: 1,
            fontFamily: '"Roboto Flex", Roboto, sans-serif'
          }}>
            Daffodil Intelligence
          </Typography>
          <Typography sx={{ 
            fontSize: '14px', 
            color: colors.onSurfaceVariant,
            fontFamily: '"Roboto Flex", Roboto, sans-serif'
          }}>
            360° Multi-Agent AI Operating System
          </Typography>
        </Box>

        <Typography sx={{ 
          fontSize: '22px', 
          fontWeight: 500, 
          mb: 0.5,
          color: colors.onSurface,
          fontFamily: '"Roboto Flex", Roboto, sans-serif'
        }}>
          {isRegister ? 'Create account' : 'Sign in'}
        </Typography>
        <Typography sx={{ 
          fontSize: '14px', 
          mb: 3,
          color: colors.onSurfaceVariant,
          fontFamily: '"Roboto Flex", Roboto, sans-serif'
        }}>
          {isRegister ? 'Use your DI account' : 'Continue to your dashboard'}
        </Typography>

        {error && (
          <Box sx={{ 
            bgcolor: 'rgba(255, 180, 171, 0.12)', 
            border: '1px solid #ffb4ab',
            borderRadius: '28px',
            p: 1.5,
            mb: 2,
            color: '#ffb4ab',
            fontSize: '14px'
          }}>
            {error}
          </Box>
        )}
        {success && (
          <Box sx={{ 
            bgcolor: 'rgba(158, 242, 194, 0.12)', 
            border: '1px solid #9ef2c2',
            borderRadius: '28px',
            p: 1.5,
            mb: 2,
            color: '#9ef2c2',
            fontSize: '14px'
          }}>
            {success}
          </Box>
        )}

        <form onSubmit={handleSubmit}>
          {isRegister && (
            <Box sx={{ mb: 2 }}>
              <Typography sx={{ 
                fontSize: '12px', 
                fontWeight: 500,
                mb: 1,
                color: colors.onSurfaceVariant,
                fontFamily: '"Roboto Flex", Roboto, sans-serif'
              }}>
                Name
              </Typography>
              <TextField 
                fullWidth 
                value={name} 
                onChange={(e) => setName(e.target.value)}
                placeholder="Enter your full name"
                sx={{
                  '& .MuiOutlinedInput-root': {
                    borderRadius: '28px',
                    bgcolor: 'transparent',
                    '& fieldset': { borderColor: '#444746' },
                    '&:hover fieldset': { borderColor: '#8d919b' },
                    '&.Mui-focused fieldset': { borderColor: '#8ab4f8', borderWidth: '2px' },
                  },
                  '& input': { 
                    color: colors.onSurface,
                    fontSize: '14px',
                    fontFamily: '"Roboto Flex", Roboto, sans-serif'
                  },
                }}
              />
            </Box>
          )}

          <Box sx={{ mb: 2 }}>
            <Typography sx={{ 
              fontSize: '12px', 
              fontWeight: 500,
              mb: 1,
              color: colors.onSurfaceVariant,
              fontFamily: '"Roboto Flex", Roboto, sans-serif'
            }}>
              Email
            </Typography>
            <TextField 
              fullWidth 
              type="email" 
              value={email} 
              onChange={(e) => setEmail(e.target.value)}
              placeholder="student@diu.edu.bd"
              sx={{
                '& .MuiOutlinedInput-root': {
                  borderRadius: '28px',
                  bgcolor: 'transparent',
                  '& fieldset': { borderColor: '#444746' },
                  '&:hover fieldset': { borderColor: '#8d919b' },
                  '&.Mui-focused fieldset': { borderColor: '#8ab4f8', borderWidth: '2px' },
                },
                '& input': { 
                  color: colors.onSurface,
                  fontSize: '14px',
                  fontFamily: '"Roboto Flex", Roboto, sans-serif'
                },
              }}
            />
          </Box>

          <Box sx={{ mb: 2 }}>
            <Typography sx={{ 
              fontSize: '12px', 
              fontWeight: 500,
              mb: 1,
              color: colors.onSurfaceVariant,
              fontFamily: '"Roboto Flex", Roboto, sans-serif'
            }}>
              Password
            </Typography>
            <TextField 
              fullWidth 
              type={showPassword ? 'text' : 'password'} 
              value={password} 
              onChange={(e) => setPassword(e.target.value)}
              placeholder={isRegister ? 'Create a password' : 'Enter your password'}
              sx={{
                '& .MuiOutlinedInput-root': {
                  borderRadius: '28px',
                  bgcolor: 'transparent',
                  '& fieldset': { borderColor: '#444746' },
                  '&:hover fieldset': { borderColor: '#8d919b' },
                  '&.Mui-focused fieldset': { borderColor: '#8ab4f8', borderWidth: '2px' },
                },
                '& input': { 
                  color: colors.onSurface,
                  fontSize: '14px',
                  fontFamily: '"Roboto Flex", Roboto, sans-serif'
                },
              }}
              InputProps={{ 
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton 
                      onClick={() => setShowPassword(!showPassword)} 
                      edge="end"
                      sx={{ color: colors.onSurfaceVariant }}
                    >
                      {showPassword ? <VisibilityOff /> : <Visibility />}
                    </IconButton>
                  </InputAdornment>
                )
              }}
            />
          </Box>

          {isRegister && (
            <Box sx={{ mb: 3 }}>
              <Typography sx={{ 
                fontSize: '12px', 
                fontWeight: 500,
                mb: 1,
                color: colors.onSurfaceVariant,
                fontFamily: '"Roboto Flex", Roboto, sans-serif'
              }}>
                Confirm Password
              </Typography>
              <TextField 
                fullWidth 
                type={showPassword ? 'text' : 'password'} 
                value={confirmPassword} 
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Confirm your password"
                sx={{
                  '& .MuiOutlinedInput-root': {
                    borderRadius: '28px',
                    bgcolor: 'transparent',
                    '& fieldset': { borderColor: '#444746' },
                    '&:hover fieldset': { borderColor: '#8d919b' },
                    '&.Mui-focused fieldset': { borderColor: '#8ab4f8', borderWidth: '2px' },
                  },
                  '& input': { 
                    color: colors.onSurface,
                    fontSize: '14px',
                    fontFamily: '"Roboto Flex", Roboto, sans-serif'
                  },
                }}
              />
            </Box>
          )}

          <Button 
            fullWidth 
            variant="contained"
            type="submit" 
            disabled={loading}
            sx={{ 
              bgcolor: '#8ab4f8', 
              color: '#131314',
              py: 1.5,
              borderRadius: '28px',
              fontWeight: 500,
              fontSize: '14px',
              fontFamily: '"Roboto Flex", Roboto, sans-serif',
              textTransform: 'none',
              '&:hover': { bgcolor: '#a8c8ff' },
              '&:disabled': { bgcolor: '#444746', color: '#8d919b' }
            }}
          >
            {loading ? <CircularProgress size={20} sx={{ color: '#131314' }} /> : (isRegister ? 'Create account' : 'Sign in')}
          </Button>
        </form>

        <Box sx={{ mt: 3, textAlign: 'center' }}>
          <Typography sx={{ 
            fontSize: '14px', 
            color: colors.onSurfaceVariant,
            mb: 2,
            fontFamily: '"Roboto Flex", Roboto, sans-serif'
          }}>
            {isRegister ? 'Already have an account?' : "Don't have an account?"}
          </Typography>
          <Button 
            fullWidth 
            variant="outlined"
            onClick={() => { setIsRegister(!isRegister); setError(''); setSuccess(''); }}
            sx={{ 
              borderColor: '#444746', 
              color: colors.onSurface,
              borderRadius: '28px',
              fontWeight: 500,
              fontSize: '14px',
              fontFamily: '"Roboto Flex", Roboto, sans-serif',
              textTransform: 'none',
              '&:hover': { 
                borderColor: '#8ab4f8', 
                bgcolor: 'rgba(138, 180, 248, 0.08)' 
              }
            }}
          >
            {isRegister ? 'Sign in instead' : 'Create account'}
          </Button>
        </Box>

        <Box sx={{ mt: 3, pt: 3, borderTop: '1px solid #444746' }}>
          <Typography sx={{ 
            fontSize: '12px', 
            color: colors.onSurfaceVariant,
            textAlign: 'center',
            mb: 2,
            fontFamily: '"Roboto Flex", Roboto, sans-serif'
          }}>
            Or continue with
          </Typography>
          <Box sx={{ display: 'flex', gap: 2 }}>
            <Button 
              fullWidth 
              variant="outlined" 
              startIcon={<Google />}
              sx={{ 
                borderColor: '#444746', 
                color: colors.onSurface,
                py: 1,
                borderRadius: '28px',
                fontWeight: 500,
                fontSize: '14px',
                fontFamily: '"Roboto Flex", Roboto, sans-serif',
                textTransform: 'none',
                '&:hover': { 
                  borderColor: '#8ab4f8', 
                  bgcolor: 'rgba(138, 180, 248, 0.08)' 
                }
              }}
            >
              Google
            </Button>
            <Button 
              fullWidth 
              variant="outlined" 
              startIcon={<GitHub />}
              sx={{ 
                borderColor: '#444746', 
                color: colors.onSurface,
                py: 1,
                borderRadius: '28px',
                fontWeight: 500,
                fontSize: '14px',
                fontFamily: '"Roboto Flex", Roboto, sans-serif',
                textTransform: 'none',
                '&:hover': { 
                  borderColor: '#8ab4f8', 
                  bgcolor: 'rgba(138, 180, 248, 0.08)' 
                }
              }}
            >
              GitHub
            </Button>
          </Box>
        </Box>
      </Box>
    </Box>
  )
}