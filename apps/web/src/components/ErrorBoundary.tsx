import { Component, ReactNode, ErrorInfo } from 'react'
import { Box, Typography, Button } from '@mui/material'
import { ErrorOutline, Refresh } from '@mui/icons-material'

interface Props {
  children: ReactNode
  fallback?: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo)
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null })
    window.location.href = '/'
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback
      }

      return (
        <Box
          sx={{
            height: '100vh',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            bgcolor: '#131314',
            color: '#e5e2e3',
            p: 4,
          }}
        >
          <ErrorOutline sx={{ fontSize: 64, color: '#ef4444', mb: 2 }} />
          <Typography variant="h5" sx={{ mb: 2, fontWeight: 500 }}>
            Something went wrong
          </Typography>
          <Typography sx={{ mb: 3, color: '#c3c6d1', textAlign: 'center', maxWidth: 400 }}>
            {this.state.error?.message || 'An unexpected error occurred'}
          </Typography>
          <Button
            onClick={this.handleReset}
            startIcon={<Refresh />}
            sx={{
              bgcolor: '#8ab4f8',
              color: '#131314',
              borderRadius: '28px',
              px: 4,
              py: 1.5,
              '&:hover': { bgcolor: '#a8c8ff' },
            }}
          >
            Go to Home
          </Button>
        </Box>
      )
    }

    return this.props.children
  }
}