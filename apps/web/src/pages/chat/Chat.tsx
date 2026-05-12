import { useState, useRef, useEffect } from 'react'
import { Box, Card, CardContent, TextField, IconButton, Typography, Avatar, Grid, Chip, Divider, ListItemButton } from '@mui/material'
import { Send, Psychology } from '@mui/icons-material'
import { useChatStore } from '../../store'
import { api } from '../../services/api'

let messageIdCounter = Date.now();

function generateMessageId(): number {
  return ++messageIdCounter;
}

const colors = {
  surface: '#131314',
  surfaceContainer: '#201f20',
  surfaceContainerHigh: '#2a2a2b',
  surfaceContainerHighest: '#353436',
  onSurface: '#e5e2e3',
  onSurfaceVariant: '#c3c6d1',
  outline: '#8d919b',
  outlineVariant: '#424750',
  primary: '#8ab4f8',
  primaryContainer: '#8ab4f8',
  secondary: '#c5c7c5',
}

const agents = [
  { id: 'supervisor', name: 'Supervisor', color: '#8ab4f8', emoji: '🎯' },
  { id: 'academic', name: 'Academic', color: '#ec4899', emoji: '📚' },
  { id: 'library', name: 'Library', color: '#22c55e', emoji: '📖' },
  { id: 'career', name: 'Career', color: '#f59e0b', emoji: '💼' },
  { id: 'coding', name: 'Coding', color: '#3b82f6', emoji: '💻' },
  { id: 'finance', name: 'Finance', color: '#8b5cf6', emoji: '💰' },
  { id: 'vision', name: 'Vision', color: '#06b6d4', emoji: '👁️' },
  { id: 'voice', name: 'Voice', color: '#ef4444', emoji: '🎤' },
  { id: 'exam', name: 'Exam', color: '#14b8a6', emoji: '📅' },
  { id: 'hostel', name: 'Hostel', color: '#f97316', emoji: '🏠' },
  { id: 'transport', name: 'Transport', color: '#84cc16', emoji: '🚌' },
  { id: 'event', name: 'Events', color: '#d946ef', emoji: '🎉' },
  { id: 'complaint', name: 'Complaint', color: '#dc2626', emoji: '📝' },
  { id: 'notification', name: 'Notification', color: '#0ea5e9', emoji: '🔔' },
  { id: 'fee', name: 'Fee', color: '#0891b2', emoji: '💵' },
  { id: 'research', name: 'Research', color: '#7c3aed', emoji: '🔬' },
  { id: 'wellness', name: 'Wellness', color: '#10b981', emoji: '🧘' },
]

export default function Chat() {
  const [input, setInput] = useState('')
  const { messages, addMessage, isLoading, setLoading, currentAgent, setAgent } = useChatStore()
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = async () => {
    if (!input.trim()) return

    addMessage({ id: generateMessageId(), role: 'user', content: input })
    setLoading(true)
    setInput('')

    try {
      const response = await api.chat(input, currentAgent)
      addMessage({
        id: generateMessageId(),
        role: 'assistant',
        content: response.response,
        agent: response.agent
      })
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred';
      addMessage({ id: generateMessageId(), role: 'assistant', content: `Error: ${errorMessage}. Please try again.` })
    }

    setLoading(false)
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <Box sx={{ height: 'calc(100vh - 120px)' }}>
      <Grid container spacing={3} sx={{ height: '100%' }}>
        <Grid item xs={12} md={3}>
          <Card sx={{ 
            bgcolor: '#191A1F', 
            border: '1px solid #444746', 
            height: '100%',
            borderRadius: '32px'
          }}>
            <CardContent>
              <Typography sx={{ 
                mb: 2, 
                fontSize: '18px',
                fontWeight: 500,
                color: colors.onSurface,
                fontFamily: '"Roboto Flex", Roboto, sans-serif'
              }}>
                Select Agent
              </Typography>
              <Grid container spacing={1}>
                {agents.map((agent) => (
                  <Grid item xs={6} key={agent.id}>
                    <ListItemButton
                      onClick={() => setAgent(agent.id)}
                      sx={{
                        borderRadius: '28px',
                        bgcolor: currentAgent === agent.id ? 'rgba(138, 180, 248, 0.12)' : 'rgba(255,255,255,0.04)',
                        border: currentAgent === agent.id ? `2px solid ${agent.color}` : '1px solid transparent',
                        flexDirection: 'column',
                        py: 1.5,
                        '&:hover': { bgcolor: 'rgba(138, 180, 248, 0.08)' }
                      }}
                    >
                      <Typography sx={{ fontSize: '1.5rem', mb: 0.5 }}>{agent.emoji}</Typography>
                      <Typography sx={{ 
                        fontSize: '12px',
                        fontWeight: currentAgent === agent.id ? 500 : 400,
                        color: colors.onSurface,
                        fontFamily: '"Roboto Flex", Roboto, sans-serif'
                      }}>
                        {agent.name}
                      </Typography>
                    </ListItemButton>
                  </Grid>
                ))}
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={9}>
          <Card sx={{ 
            bgcolor: '#191A1F', 
            border: '1px solid #444746', 
            height: '100%', 
            display: 'flex', 
            flexDirection: 'column',
            borderRadius: '32px'
          }}>
            <CardContent sx={{ flexGrow: 1, overflow: 'auto', pb: 2 }}>
              {messages.length === 0 ? (
                <Box sx={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column' }}>
                  <Psychology sx={{ fontSize: 60, color: colors.primary, mb: 2 }} />
                  <Typography sx={{ 
                    fontSize: '22px',
                    fontWeight: 500,
                    color: colors.onSurfaceVariant,
                    fontFamily: '"Roboto Flex", Roboto, sans-serif'
                  }}>
                    How can I help you today?
                  </Typography>
                  <Typography sx={{ 
                    fontSize: '14px',
                    color: colors.onSurfaceVariant,
                    fontFamily: '"Roboto Flex", Roboto, sans-serif',
                    mt: 1
                  }}>
                    Ask about courses, books, jobs, or anything!
                  </Typography>
                </Box>
              ) : (
                messages.map((msg) => (
                  <Box key={msg.id} sx={{ mb: 3, display: 'flex', gap: 2 }}>
                    <Avatar sx={{ bgcolor: msg.role === 'user' ? colors.primary : '#22c55e', color: '#131314' }}>
                      {msg.role === 'user' ? 'U' : 'AI'}
                    </Avatar>
                    <Box sx={{ flexGrow: 1 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                        <Typography sx={{ 
                          fontSize: '14px',
                          fontWeight: 600,
                          color: colors.onSurface,
                          fontFamily: '"Roboto Flex", Roboto, sans-serif'
                        }}>
                          {msg.role === 'user' ? 'You' : 'Daffodil Intelligence'}
                        </Typography>
                        {msg.agent && (
                          <Chip 
                            label={msg.agent} 
                            size="small" 
                            sx={{ 
                              bgcolor: 'rgba(138, 180, 248, 0.12)', 
                              color: colors.primary,
                              borderRadius: '9999px',
                              fontSize: '11px',
                              fontFamily: '"Roboto Flex", Roboto, sans-serif'
                            }} 
                          />
                        )}
                      </Box>
                      <Typography sx={{ 
                        whiteSpace: 'pre-wrap', 
                        lineHeight: 1.7,
                        color: colors.onSurface,
                        fontFamily: '"Roboto Flex", Roboto, sans-serif',
                        fontSize: '14px'
                      }}>
                        {msg.content}
                      </Typography>
                    </Box>
                  </Box>
                ))
              )}
              {isLoading && (
                <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
                  <Avatar sx={{ bgcolor: '#22c55e', color: '#131314' }}>AI</Avatar>
                  <Typography sx={{ color: colors.onSurfaceVariant }}>
                    Thinking...
                  </Typography>
                </Box>
              )}
              <div ref={messagesEndRef} />
            </CardContent>

            <Divider sx={{ borderColor: '#444746' }} />
            <Box sx={{ p: 2, display: 'flex', gap: 2 }}>
              <TextField
                fullWidth
                multiline
                maxRows={4}
                placeholder="Type your message..."
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={handleKeyPress}
                disabled={isLoading}
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
              <IconButton 
                onClick={handleSend} 
                disabled={isLoading || !input.trim()} 
                sx={{ 
                  bgcolor: colors.primary, 
                  color: '#131314', 
                  borderRadius: '28px',
                  width: 48,
                  height: 48,
                  '&:hover': { bgcolor: '#a8c8ff' },
                  '&:disabled': { bgcolor: '#444746', color: '#8d919b' }
                }}
              >
                <Send />
              </IconButton>
            </Box>
          </Card>
        </Grid>
      </Grid>
    </Box>
  )
}