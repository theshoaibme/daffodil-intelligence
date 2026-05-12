import { useState } from 'react'
import { Box, Card, CardContent, Typography, Button, IconButton, Grid, List, ListItem, ListItemText, Chip } from '@mui/material'
import { Mic, MicOff, Videocam, VideocamOff, ScreenShare, CallEnd } from '@mui/icons-material'

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
      <Typography variant="h4" sx={{ mb: 3, fontWeight: 700 }}>Live Voice Chat</Typography>

      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <Card sx={{ bgcolor: 'background.paper', border: '1px solid #334155', minHeight: 500 }}>
            <CardContent sx={{ height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
              {!isCallActive ? (
                <Box sx={{ textAlign: 'center' }}>
                  <Videocam sx={{ fontSize: 80, color: '#6366f1', mb: 3 }} />
                  <Typography variant="h5" sx={{ mb: 2 }}>Start a Live Voice Conversation</Typography>
                  <Typography variant="body2" sx={{ color: '#94a3b8', mb: 3 }}>
                    Connect with DI's AI using voice. Get instant responses, ask questions, and get help in real-time.
                  </Typography>
                  <Button variant="contained" size="large" startIcon={<Mic />} onClick={startCall} sx={{ bgcolor: '#6366f1' }}>
                    Start Voice Chat
                  </Button>
                </Box>
              ) : (
                <Box sx={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column' }}>
                  <Box sx={{ flexGrow: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', bgcolor: '#0f172a', borderRadius: 2, mb: 2 }}>
                    <Typography sx={{ color: '#94a3b8' }}>AI is listening...</Typography>
                  </Box>

                  <Box sx={{ display: 'flex', justifyContent: 'center', gap: 2, mb: 2 }}>
                    <IconButton onClick={() => setIsMuted(!isMuted)} sx={{ bgcolor: isMuted ? '#ef4444' : '#334155', color: 'white' }}>
                      {isMuted ? <MicOff /> : <Mic />}
                    </IconButton>
                    <IconButton onClick={() => setIsVideoOn(!isVideoOn)} sx={{ bgcolor: !isVideoOn ? '#ef4444' : '#334155', color: 'white' }}>
                      {isVideoOn ? <Videocam /> : <VideocamOff />}
                    </IconButton>
                    <IconButton sx={{ bgcolor: '#334155', color: 'white' }}><ScreenShare /></IconButton>
                    <IconButton onClick={endCall} sx={{ bgcolor: '#ef4444', color: 'white' }}><CallEnd /></IconButton>
                  </Box>

                  <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                    {quickPrompts.map((p, i) => (
                      <Chip key={i} label={p} onClick={() => setTranscript([...transcript, `You: ${p}`])} sx={{ cursor: 'pointer' }} />
                    ))}
                  </Box>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card sx={{ bgcolor: 'background.paper', border: '1px solid #334155', height: 500 }}>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>Transcript</Typography>
              <List>
                {transcript.length === 0 ? (
                  <Typography sx={{ color: '#94a3b8', textAlign: 'center', mt: 4 }}>No transcript yet</Typography>
                ) : (
                  transcript.map((t, i) => (
                    <ListItem key={i} sx={{ bgcolor: '#334155', borderRadius: 1, mb: 1 }}>
                      <ListItemText primary={t} />
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