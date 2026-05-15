import { Box, Typography } from '@mui/material'

function App() {
  return (
    <Box sx={{
      minHeight: '100vh',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      bgcolor: '#0a0a0a',
      color: '#ffffff'
    }}>
      <Typography variant="h3" sx={{ mb: 2 }}>
        Daffodil Intelligence API
      </Typography>
      <Typography sx={{ color: '#888888' }}>
        Backend services ready. See API documentation for endpoints.
      </Typography>
    </Box>
  )
}

export default App