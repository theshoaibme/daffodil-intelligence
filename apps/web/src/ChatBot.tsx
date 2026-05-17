import React, { useEffect, useMemo, useRef, useState } from 'react'
import { Box, Button, CircularProgress, IconButton, Paper, TextField, Typography } from '@mui/material'
import ChatIcon from '@mui/icons-material/Chat'
import CloseIcon from '@mui/icons-material/Close'
import SendIcon from '@mui/icons-material/Send'

interface ChatMessage {
  id: string
  author: 'assistant' | 'user'
  text: string
}

const defaultMessage = 'হ্যালো! আমি ড্যাফোডিল ইন্টেলিজেন্স। কীভাবে সাহায্য করতে পারি?'
const apiUrl = '/api/chat'

const ChatBot: React.FC = () => {
  const [open, setOpen] = useState(false)
  const [input, setInput] = useState('')
  const [messages, setMessages] = useState<ChatMessage[]>([
    { id: 'initial-assistant', author: 'assistant', text: defaultMessage }
  ])
  const [loading, setLoading] = useState(false)
  const scrollRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    if (!scrollRef.current) return
    scrollRef.current.scrollTop = scrollRef.current.scrollHeight
  }, [messages, open])

  const historyPayload = useMemo(
    () => messages.map((message) => ({ role: message.author, content: message.text })),
    [messages]
  )

  const handleSend = async () => {
    const trimmed = input.trim()
    if (!trimmed || loading) return

    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      author: 'user',
      text: trimmed
    }

    setMessages((prev) => [...prev, userMessage])
    setInput('')
    setLoading(true)

    try {
      const response = await fetch(apiUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: trimmed, history: historyPayload })
      })

      if (!response.ok) {
        const errorText = await response.text()
        throw new Error(errorText || `${response.status} ${response.statusText}`)
      }

      const data = await response.json()
      const assistantText = data.reply ?? 'দুঃখিত, সার্ভার থেকে উত্তর পাওয়া যায়নি।'

      setMessages((prev) => [
        ...prev,
        { id: `assistant-${Date.now()}`, author: 'assistant', text: assistantText }
      ])
    } catch (error: any) {
      setMessages((prev) => [
        ...prev,
        {
          id: `assistant-error-${Date.now()}`,
          author: 'assistant',
          text: 'দুঃখিত, আমি এখনই উত্তর দিতে পারছি না। পরে আবার চেষ্টা করুন।'
        }
      ])
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (event: React.KeyboardEvent<HTMLDivElement>) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      handleSend()
    }
  }

  return (
    <>
      <Box
        sx={{
          position: 'fixed',
          right: 24,
          bottom: 24,
          zIndex: 1400,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'flex-end'
        }}
      >
        {open ? (
          <Paper
            elevation={24}
            sx={{
              width: 360,
              maxHeight: 560,
              display: 'flex',
              flexDirection: 'column',
              overflow: 'hidden',
              borderRadius: 3,
              bgcolor: 'background.paper'
            }}
          >
            <Box
              sx={{
                px: 2,
                py: 1.5,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                borderBottom: '1px solid rgba(255,255,255,0.08)',
                bgcolor: 'primary.main',
                color: 'primary.contrastText'
              }}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <ChatIcon fontSize="small" />
                <Typography variant="subtitle1">ড্যাফোডিল চ্যাটবট</Typography>
              </Box>
              <IconButton size="small" onClick={() => setOpen(false)} sx={{ color: 'inherit' }}>
                <CloseIcon fontSize="small" />
              </IconButton>
            </Box>

            <Box
              ref={scrollRef}
              sx={{
                flex: 1,
                px: 2,
                py: 2,
                overflowY: 'auto',
                bgcolor: 'rgba(15, 23, 42, 0.95)'
              }}
            >
              {messages.map((message) => (
                <Box
                  key={message.id}
                  sx={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: message.author === 'user' ? 'flex-end' : 'flex-start',
                    mb: 1.5
                  }}
                >
                  <Box
                    sx={{
                      maxWidth: '100%',
                      p: 1.5,
                      borderRadius: 2,
                      bgcolor: message.author === 'user' ? 'primary.main' : 'grey.800',
                      color: message.author === 'user' ? 'primary.contrastText' : 'grey.100',
                      boxShadow: 1
                    }}
                  >
                    <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                      {message.text}
                    </Typography>
                  </Box>
                </Box>
              ))}
            </Box>

            <Box sx={{ px: 2, py: 1.5, borderTop: '1px solid rgba(255,255,255,0.08)' }}>
              <TextField
                value={input}
                onChange={(event) => setInput(event.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="আপনার প্রশ্ন লিখুন..."
                multiline
                maxRows={4}
                fullWidth
                disabled={loading}
                size="small"
                sx={{ mb: 1 }}
              />
              <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                <Button
                  variant="contained"
                  color="primary"
                  onClick={handleSend}
                  disabled={!input.trim() || loading}
                  fullWidth
                  endIcon={<SendIcon />}
                >
                  পাঠান
                </Button>
                {loading && <CircularProgress size={28} />}
              </Box>
            </Box>
          </Paper>
        ) : (
          <Button
            variant="contained"
            color="secondary"
            startIcon={<ChatIcon />}
            onClick={() => setOpen(true)}
            sx={{ borderRadius: '999px', textTransform: 'none', px: 3, py: 1.5 }}
          >
            Chat Now
          </Button>
        )}
      </Box>
    </>
  )
}

export default ChatBot
