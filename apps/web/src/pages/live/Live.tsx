import { useState } from 'react'
import { Box, Card, CardContent, Typography, Button, IconButton, Grid, List, ListItem, ListItemText, Chip } from '@mui/material'
import { Mic, MicOff, Videocam, VideocamOff, ScreenShare, CallEnd } from '@mui/icons-material'

const colors = {
  surface: '#131314',
  onSurface: '#e5e2e3',
  onSurfaceVariant: '#c3c6d1',
  primary: '#8ab4f8',
  primaryContainer: '#8ab4f8',
}

export default function Live() {
  const [isMuted, setIsMuted] = useState(false)
  const [isVideoOn, setIsVideoOn] = useState(true)
  const [isCallActive, setIsCallActive] = useState(false)
  const [transcript, setTranscript] = useState<string[]>([])

  const startCall = () => setIsCallActive(true)
  const endCall = () => { setIsCallActive(false); setTranscript([]) }

  const quickPrompts = [
    "Explain this concept",
    "Help with this problem",
    "What's my current status?",
    "Show me related resources"
  ]

  return (
    <Box>
      <Typography sx={{ 
        mb: 3, 
        fontSize: '28px',
        fontWeight: 500,
        color: colors.onSurface,
        fontFamily: '"Roboto Flex", Roboto, sans-serif'
      }}>
        Live Voice Chat
      </Typography>

      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <Card sx={{ 
            bgcolor: '#191A1F', 
            border: '1px solid #444746', 
            minHeight: 500,
            borderRadius: '32px'
          }}>
            <CardContent sx={{ height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', p: 4 }}>
              {!isCallActive ? (
                <Box sx={{ textAlign: 'center' }}>
                  <Videocam sx={{ fontSize: 80, color: colors.primary, mb: 3 }} />
                  <Typography sx={{ 
                    mb: 2,
                    fontSize: '22px',
                    fontWeight: 500,
                    color: colors.onSurface,
                    fontFamily: '"Roboto Flex", Roboto, sans-serif'
                  }}>
                    Start a Live Voice Conversation
                  </Typography>
                  <Typography sx={{ 
                    color: colors.onSurfaceVariant,
                    fontFamily: '"Roboto Flex", Roboto, sans-serif',
                    fontSize: '14px',
                    mb: 3
                  }}>
                    Connect with DI's AI using voice. Get instant responses, ask questions, and get help in real-time.
                  </Typography>
                  <Button 
                    variant="contained" 
                    startIcon={<Mic />} 
                    onClick={startCall}
                    sx={{
                      bgcolor: colors.primary,
                      color: '#131314',
                      borderRadius: '16px',
                      px: 4,
                      py: 1.5,
                      fontWeight: 500,
                      fontSize: '14px',
                      fontFamily: '"Roboto Flex", Roboto, sans-serif',
                      textTransform: 'none',
                      '&:hover': { bgcolor: '#a8c8ff' }
                    }}
                  >
                    Start Voice Chat
                  </Button>
                </Box>
              ) : (
                <Box sx={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column' }}>
                  <Box sx={{ 
                    flexGrow: 1, 
                    display: 'flex', 
                    alignItems: 'center', 
                    justifyContent: 'center', 
                    bgcolor: '#0e0e0f', 
                    borderRadius: '16px', 
                    mb: 2 
                  }}>
                    <Typography sx={{ 
                      color: colors.onSurfaceVariant,
                      fontFamily: '"Roboto Flex", Roboto, sans-serif',
                      fontSize: '14px'
                    }}>
                      AI is listening...
                    </Typography>
                  </Box>

                  <Box sx={{ display: 'flex', justifyContent: 'center', gap: 2, mb: 2 }}>
                    <IconButton 
                      onClick={() => setIsMuted(!isMuted)} 
                      sx={{ 
                        bgcolor: isMuted ? '#ef4444' : '#444746', 
                        color: 'white',
borderRadius: '28px',
                width: 52,
                height: 52,
                        '&:hover': { bgcolor: isMuted ? '#dc2626' : '#555b67' }
                      }}
                    >
                      {isMuted ? <MicOff /> : <Mic />}
                    </IconButton>
                    <IconButton 
                      onClick={() => setIsVideoOn(!isVideoOn)} 
                      sx={{ 
                        bgcolor: !isVideoOn ? '#ef4444' : '#444746', 
                        color: 'white',
borderRadius: '28px',
                width: 52,
                height: 52,
                        '&:hover': { bgcolor: !isVideoOn ? '#dc2626' : '#555b67' }
                      }}
                    >
                      {isVideoOn ? <Videocam /> : <VideocamOff />}
                    </IconButton>
                    <IconButton 
                      sx={{ 
                        bgcolor: '#444746', 
                        color: 'white',
borderRadius: '28px',
                width: 52,
                height: 52,
                        '&:hover': { bgcolor: '#555b67' }
                      }}
                    >
                      <ScreenShare />
                    </IconButton>
                    <IconButton 
                      onClick={endCall} 
                      sx={{ 
                        bgcolor: '#ef4444', 
                        color: 'white',
borderRadius: '28px',
                width: 52,
                height: 52,
                        '&:hover': { bgcolor: '#dc2626' }
                      }}
                    >
                      <CallEnd />
                    </IconButton>
                  </Box>

                  <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                    {quickPrompts.map((p, i) => (
                      <Chip 
                        key={i} 
                        label={p} 
                        onClick={() => setTranscript([...transcript, `You: ${p}`])}
                        sx={{ 
                          cursor: 'pointer',
                          bgcolor: 'rgba(138, 180, 248, 0.12)',
                          color: colors.primary,
                          borderRadius: '9999px',
                          fontSize: '12px',
                          fontFamily: '"Roboto Flex", Roboto, sans-serif',
                          '&:hover': { bgcolor: 'rgba(138, 180, 248, 0.2)' }
                        }} 
                      />
                    ))}
                  </Box>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card sx={{ 
            bgcolor: '#191A1F', 
            border: '1px solid #444746', 
            height: 500,
            borderRadius: '32px'
          }}>
            <CardContent>
              <Typography sx={{ 
                mb: 2,
                fontSize: '16px',
                fontWeight: 500,
                color: colors.onSurface,
                fontFamily: '"Roboto Flex", Roboto, sans-serif'
              }}>
                Transcript
              </Typography>
              <List>
                {transcript.length === 0 ? (
                  <Typography sx={{ 
                    color: colors.onSurfaceVariant, 
                    textAlign: 'center', 
                    mt: 4,
                    fontFamily: '"Roboto Flex", Roboto, sans-serif',
                    fontSize: '14px'
                  }}>
                    No transcript yet
                  </Typography>
                ) : (
                  transcript.map((t, i) => (
                    <ListItem key={i} sx={{ 
                      bgcolor: '#2a2a2b', 
                      borderRadius: '16px', 
                      mb: 1 
                    }}>
                      <ListItemText 
                        primary={t}
                        primaryTypographyProps={{
                          sx: { 
                            color: colors.onSurface,
                            fontFamily: '"Roboto Flex", Roboto, sans-serif',
                            fontSize: '14px'
                          }
                        }}
                      />
                    </ListItem>
                  ))
                )}
              </List>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  )
}