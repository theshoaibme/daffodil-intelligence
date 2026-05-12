import { useState, useRef, useEffect } from 'react'
import { Box, Card, CardContent, TextField, IconButton, Typography, Chip, Avatar, List, ListItem, ListItemAvatar, ListItemText, Divider, Grid } from '@mui/material'
import { Send, Psychology, School, LibraryBooks, Work, Code, AttachMoney, Visibility, Mic } from '@mui/icons-material'
import { useChatStore } from '../../store'
import { api } from '../../services/api'

const agents = [
  { id: 'supervisor', name: 'Supervisor', icon: <Psychology />, color: '#6366f1' },
  { id: 'academic', name: 'Academic', icon: <School />, color: '#ec4899' },
  { id: 'library', name: 'Library', icon: <LibraryBooks />, color: '#22c55e' },
  { id: 'career', name: 'Career', icon: <Work />, color: '#f59e0b' },
  { id: 'coding', name: 'Coding', icon: <Code />, color: '#3b82f6' },
  { id: 'finance', name: 'Finance', icon: <AttachMoney />, color: '#8b5cf6' },
  { id: 'vision', name: 'Vision', icon: <Visibility />, color: '#06b6d4' },
  { id: 'voice', name: 'Voice', icon: <Mic />, color: '#ef4444' },
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

    addMessage({ id: Date.now(), role: 'user', content: input })
    setLoading(true)
    setInput('')

    try {
      const response = await api.chat(input, currentAgent)
      addMessage({
        id: Date.now() + 1,
        role: 'assistant',
        content: response.response,
        agent: response.agent
      })
    } catch (err) {
      addMessage({ id: Date.now() + 1, role: 'assistant', content: 'Sorry, I encountered an error. Please try again.' })
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
          <Card sx={{ bgcolor: 'background.paper', border: '1px solid #334155', height: '100%' }}>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>Select Agent</Typography>
              <List>
                {agents.map((agent) => (
                  <ListItem
                    button
                    key={agent.id}
                    onClick={() => setAgent(agent.id)}
                    sx={{
                      mb: 1,
                      borderRadius: 2,
                      bgcolor: currentAgent === agent.id ? `${agent.color}20` : 'transparent',
                      border: currentAgent === agent.id ? `1px solid ${agent.color}` : '1px solid transparent'
                    }}
                  >
                    <ListItemAvatar>
                      <Avatar sx={{ bgcolor: agent.color }}>{agent.icon}</Avatar>
                    </ListItemAvatar>
                    <ListItemText primary={agent.name} />
                  </ListItem>
                ))}
              </List>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={9}>
          <Card sx={{ bgcolor: 'background.paper', border: '1px solid #334155', height: '100%', display: 'flex', flexDirection: 'column' }}>
            <CardContent sx={{ flexGrow: 1, overflow: 'auto', pb: 2 }}>
              {messages.length === 0 ? (
                <Box sx={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column' }}>
                  <Psychology sx={{ fontSize: 60, color: '#6366f1', mb: 2 }} />
                  <Typography variant="h5" sx={{ color: '#94a3b8' }}>How can I help you today?</Typography>
                  <Typography variant="body2" sx={{ color: '#64748b', mt: 1 }}>Ask about courses, books, jobs, or anything!</Typography>
                </Box>
              ) : (
                messages.map((msg) => (
                  <Box key={msg.id} sx={{ mb: 3, display: 'flex', gap: 2 }}>
                    <Avatar sx={{ bgcolor: msg.role === 'user' ? '#6366f1' : '#22c55e' }}>
                      {msg.role === 'user' ? 'U' : 'AI'}
                    </Avatar>
                    <Box sx={{ flexGrow: 1 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                        <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                          {msg.role === 'user' ? 'You' : 'Daffodil Intelligence'}
                        </Typography>
                        {msg.agent && <Chip label={msg.agent} size="small" sx={{ bgcolor: '#6366f120', color: '#6366f1' }} />}
                      </Box>
                      <Typography sx={{ whiteSpace: 'pre-wrap', lineHeight: 1.7 }}>{msg.content}</Typography>
                    </Box>
                  </Box>
                ))
              )}
              {isLoading && (
                <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
                  <Avatar sx={{ bgcolor: '#22c55e' }}>AI</Avatar>
                  <Typography sx={{ color: '#94a3b8' }}>Thinking...</Typography>
                </Box>
              )}
              <div ref={messagesEndRef} />
            </CardContent>

            <Divider />
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
              />
              <IconButton color="primary" onClick={handleSend} disabled={isLoading || !input.trim()} sx={{ bgcolor: '#6366f1', color: 'white', '&:hover': { bgcolor: '#4f46e5' } }}>
                <Send />
              </IconButton>
            </Box>
          </Card>
        </Grid>
      </Grid>
    </Box>
  )
}