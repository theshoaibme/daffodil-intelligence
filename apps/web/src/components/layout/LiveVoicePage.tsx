import { useState, useRef, useEffect } from 'react'
import { Box, Card, CardContent, Typography, Button, IconButton, Grid, List, ListItem, ListItemText, Chip, Alert, Select, MenuItem, FormControl, InputLabel } from '@mui/material'
import { Mic, MicOff, CallEnd, StopCircle, PlayArrow, Settings, Videocam } from '@mui/icons-material'

const colors = {
  surface: '#131314',
  onSurface: '#e5e2e3',
  onSurfaceVariant: '#c3c6d1',
  primary: '#8ab4f8',
  success: '#4caf50',
  error: '#ef4444',
}

interface TranscriptItem {
  id: number
  type: 'user' | 'ai'
  text: string
  timestamp: Date
}

const FILLERS_EN = [
  "Hmm..., ",
  "Let me think... ",
  "Okay, here's what I found: ",
  "So, ",
  "Well, ",
  "Let me check that for you... ",
  "Sure thing! ",
  "That's a good question! ",
]

const FILLERS_BN = [
  "হুম, ",
  "চিন্তা করি... ",
  "ঠিক আছে, ",
  "তাহলে, ",
  "আচ্ছা, ",
  "একটু দেখি... ",
  "অবশ্যই! ",
  "চমৎকার প্রশ্ন! ",
]

const selectBestVoice = (lang: string): SpeechSynthesisVoice | null => {
  if (!window.speechSynthesis) return null
  const voices = window.speechSynthesis.getVoices()
  const langPrefix = lang.split('-')[0]
  
  const preferred = voices.find(v => 
    v.lang.startsWith(langPrefix) && (v.localService || v.name.includes('Premium') || v.name.includes('Neural'))
  )
  return preferred || voices.find(v => v.lang.startsWith(langPrefix)) || null
}

const addFiller = (text: string, lang: string): string => {
  if (!text.trim()) return text
  
  const fillers = lang.startsWith('bn') ? FILLERS_BN : FILLERS_EN
  const isQuestion = text.trim().endsWith('?')
  const isGreeting = /^(hi|hello|hey|হ্যালো|হাই|নমস্কার)/i.test(text.trim())
  
  if (!isQuestion && !isGreeting && Math.random() < 0.35) {
    const filler = fillers[Math.floor(Math.random() * fillers.length)]
    return filler + text
  }
  return text
}

const preprocessText = (text: string): string => {
  let processed = text
    .replace(/\s+/g, ' ')
    .replace(/([.!?]){2,}/g, '.')
    .replace(/,+/g, ',')
  
  const length = processed.length
  if (length < 30) {
    processed = processed.charAt(0).toUpperCase() + processed.slice(1)
  }
  
  return processed
}

export default function Live() {
  const [isMuted, setIsMuted] = useState(false)
  const [isCallActive, setIsCallActive] = useState(false)
  const [isListening, setIsListening] = useState(false)
  const [isSpeaking, setIsSpeaking] = useState(false)
  const [transcript, setTranscript] = useState<TranscriptItem[]>([])
  const [error, setError] = useState<string | null>(null)
  const [showSettings, setShowSettings] = useState(false)
  const [selectedLanguage, setSelectedLanguage] = useState('en-US')
  const [useWebSocket, setUseWebSocket] = useState(true)

  const recognitionRef = useRef<any>(null)
  const transcriptIdRef = useRef(0)
  const isSpeakingRef = useRef(false)
  const wsRef = useRef<WebSocket | null>(null)
  const audioContextRef = useRef<AudioContext | null>(null)
  const audioQueueRef = useRef<AudioBuffer[]>([])
  const isPlayingRef = useRef(false)

  useEffect(() => {
    const loadVoices = () => {
      if (window.speechSynthesis) {
        window.speechSynthesis.getVoices()
      }
    }
    
    loadVoices()
    if (window.speechSynthesis) {
      window.speechSynthesis.onvoiceschanged = loadVoices
    }

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop()
        recognitionRef.current = null
      }
      if (window.speechSynthesis) {
        window.speechSynthesis.cancel()
      }
      if (wsRef.current) {
        wsRef.current.close()
      }
      if (audioContextRef.current) {
        audioContextRef.current.close()
      }
    }
  }, [])

  const initAudioContext = () => {
    if (!audioContextRef.current) {
      audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)()
    }
    return audioContextRef.current
  }

  const playAudioChunk = async (base64Audio: string) => {
    try {
      const audioContext = initAudioContext()
      
      const binaryString = atob(base64Audio)
      const bytes = new Uint8Array(binaryString.length)
      for (let i = 0; i < binaryString.length; i++) {
        bytes[i] = binaryString.charCodeAt(i)
      }
      
      const audioBuffer = await audioContext.decodeAudioData(bytes.buffer)
      audioQueueRef.current.push(audioBuffer)
      
      if (!isPlayingRef.current) {
        playNextAudio()
      }
    } catch (err) {
      console.error('Error playing audio:', err)
    }
  }

  const playNextAudio = () => {
    if (audioQueueRef.current.length === 0) {
      isPlayingRef.current = false
      isSpeakingRef.current = false
      setIsSpeaking(false)
      return
    }

    isPlayingRef.current = true
    const audioContext = audioContextRef.current
    if (!audioContext) return

    const buffer = audioQueueRef.current.shift()
    if (!buffer) {
      playNextAudio()
      return
    }

    const source = audioContext.createBufferSource()
    source.buffer = buffer
    source.connect(audioContext.destination)
    
    source.onended = () => {
      if (audioQueueRef.current.length > 0) {
        playNextAudio()
      } else {
        isSpeakingRef.current = false
        setIsSpeaking(false)
      }
    }

    source.start(0)
  }

  const connectWebSocket = (userId: number = 1) => {
    return new Promise<void>((resolve, reject) => {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const wsUrl = `ws://localhost:8000/voice/ws/voice/${userId}`
      
      const ws = new WebSocket(wsUrl)
      wsRef.current = ws

      ws.onopen = () => {
        console.log('WebSocket connected')
        resolve()
      }

      ws.onmessage = async (event) => {
        const data = JSON.parse(event.data)
        
        if (data.type === 'connected') {
          console.log('Session connected:', data.session)
        } else if (data.type === 'audio_chunk') {
          if (data.audio) {
            isSpeakingRef.current = true
            setIsSpeaking(true)
            await playAudioChunk(data.audio)
          }
        } else if (data.type === 'complete') {
          isSpeakingRef.current = false
          setIsSpeaking(false)
        } else if (data.type === 'interrupted') {
          audioQueueRef.current = []
          isPlayingRef.current = false
          isSpeakingRef.current = false
          setIsSpeaking(false)
        } else if (data.type === 'interrupt_ack') {
          console.log('Interrupt acknowledged')
        } else if (data.type === 'error') {
          console.error('WebSocket error:', data.message)
        }
      }

      ws.onerror = (err) => {
        console.error('WebSocket error:', err)
        reject(err)
      }

      ws.onclose = () => {
        console.log('WebSocket closed')
        wsRef.current = null
      }
    })
  }

  const sendInterrupt = () => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'interrupt' }))
      audioQueueRef.current = []
      isPlayingRef.current = false
    }
    if (window.speechSynthesis) {
      window.speechSynthesis.cancel()
    }
    isSpeakingRef.current = false
    setIsSpeaking(false)
  }

  const sendTextMessage = async (text: string) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'text',
        data: text,
        language: selectedLanguage
      }))
    }
  }

  const disconnectWebSocket = () => {
    if (wsRef.current) {
      wsRef.current.send(JSON.stringify({ type: 'end' }))
      wsRef.current.close()
      wsRef.current = null
    }
    audioQueueRef.current = []
    isPlayingRef.current = false
  }

  const requestMicrophonePermission = async (): Promise<boolean> => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      stream.getTracks().forEach(track => track.stop())
      return true
    } catch (err) {
      console.error('Microphone permission denied:', err)
      return false
    }
  }

  const initSpeechRecognition = async () => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
    
    if (!SpeechRecognition) {
      setError('Speech recognition not supported. Please use Chrome or Edge.')
      return false
    }

    const hasPermission = await requestMicrophonePermission()
    if (!hasPermission) {
      setError('Microphone access denied. Please allow microphone access in your browser settings and refresh the page.')
      return false
    }

    recognitionRef.current = new SpeechRecognition()
    recognitionRef.current.continuous = true
    recognitionRef.current.interimResults = true
    recognitionRef.current.lang = selectedLanguage

    recognitionRef.current.onstart = () => {
      setIsListening(true)
      setError(null)
    }

    recognitionRef.current.onresult = async (event: any) => {
      sendInterrupt()
      
      const result = event.results[event.results.length - 1]
      const transcriptText = result[0].transcript.trim()

      if (result.isFinal && transcriptText) {
        await processUserSpeech(transcriptText)
      }
    }

    recognitionRef.current.onerror = (event: any) => {
      console.error('Speech error:', event.error)
      
      if (event.error === 'not-allowed') {
        setError('Microphone access denied. Please click the lock icon in your browser address bar and allow microphone access, then refresh the page.')
      } else if (event.error === 'security') {
        setError('Speech recognition requires HTTPS or localhost. Please use a secure connection.')
      } else if (event.error !== 'aborted' && event.error !== 'no-speech') {
        setError(`Speech error: ${event.error}`)
      }
    }

    recognitionRef.current.onend = () => {
      if (isCallActive && !isMuted && recognitionRef.current) {
        try {
          recognitionRef.current.start()
        } catch (e) {
          console.log('Recognition restart failed')
        }
      }
    }

    return true
  }

  const processUserSpeech = async (text: string) => {
    if (!text.trim()) return

    const userTranscript: TranscriptItem = {
      id: transcriptIdRef.current++,
      type: 'user',
      text,
      timestamp: new Date()
    }
    setTranscript(prev => [...prev, userTranscript])

    try {
      if (useWebSocket && wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        isSpeakingRef.current = true
        setIsSpeaking(true)
        
        await sendTextMessage(text)
        
        setTimeout(() => {
          if (wsRef.current) {
            wsRef.current.send(JSON.stringify({ type: 'interrupt' }))
          }
        }, 5000)
        
      } else {
        setIsSpeaking(true)
        isSpeakingRef.current = true
        
        const response = await fetch('http://localhost:8000/api/agents/gemini/chat/simple', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: text })
        })

        const data = await response.json()
        let aiResponse = data.response || data.error || 'Sorry, I could not process that request.'
        
        aiResponse = preprocessText(aiResponse)
        aiResponse = addFiller(aiResponse, selectedLanguage)

        const aiTranscript: TranscriptItem = {
          id: transcriptIdRef.current++,
          type: 'ai',
          text: aiResponse,
          timestamp: new Date()
        }
        setTranscript(prev => [...prev, aiTranscript])

        speakText(aiResponse)
      }
    } catch (err) {
      console.error('Error:', err)
      const errorResponse = preprocessText('Sorry, I encountered an error. Please try again.')
      const errorTranscript: TranscriptItem = {
        id: transcriptIdRef.current++,
        type: 'ai',
        text: errorResponse,
        timestamp: new Date()
      }
      setTranscript(prev => [...prev, errorTranscript])
    }
  }

  const speakText = (text: string) => {
    if (!window.speechSynthesis) return

    window.speechSynthesis.cancel()

    const sentences = text.match(/[^.!?।]+[.!?।]+/g) || [text]
    if (sentences.length === 0 || !sentences[0].trim()) {
      sentences[0] = text
    }

    const voice = selectBestVoice(selectedLanguage)
    const baseRate = text.length > 200 ? 1.1 : 1.05
    const basePitch = 1.02

    let completedCount = 0
    const totalSentences = sentences.length

    sentences.forEach((sentence, index) => {
      const cleanSentence = sentence.trim()
      if (!cleanSentence) return

      setTimeout(() => {
        if (!isSpeakingRef.current && index > 0) return

        const utterance = new SpeechSynthesisUtterance(cleanSentence)
        utterance.lang = selectedLanguage
        
        const wordCount = cleanSentence.split(/\s+/).length
        const rate = wordCount < 5 ? baseRate + 0.05 : (wordCount > 20 ? baseRate - 0.05 : baseRate)
        utterance.rate = rate
        utterance.pitch = basePitch
        utterance.volume = 1.0
        
        if (voice) {
          utterance.voice = voice
        }

        utterance.onstart = () => {
          isSpeakingRef.current = true
          setIsSpeaking(true)
        }
        
        utterance.onend = () => {
          completedCount++
          if (completedCount >= totalSentences) {
            isSpeakingRef.current = false
            setIsSpeaking(false)
          }
        }
        
        utterance.onerror = () => {
          completedCount++
          if (completedCount >= totalSentences) {
            isSpeakingRef.current = false
            setIsSpeaking(false)
          }
        }

        window.speechSynthesis.speak(utterance)
      }, index * 100)
    })
  }

  const startCall = async () => {
    try {
      setError(null)
      setTranscript([])

      const initialized = await initSpeechRecognition()
      if (!initialized) return

      setIsCallActive(true)

      if (useWebSocket) {
        try {
          await connectWebSocket(1)
        } catch (wsErr) {
          console.warn('WebSocket connection failed, using HTTP fallback:', wsErr)
        }
      }

      setTimeout(() => {
        if (recognitionRef.current) {
          try {
            recognitionRef.current.start()
          } catch (e) {
            console.error('Failed to start recognition:', e)
          }
        }
      }, 500)

      const welcomeMessage = "Hello! I'm your AI assistant. How can I help you today?"
      
      setTimeout(() => {
        if (useWebSocket && wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
          sendTextMessage(welcomeMessage)
        } else {
          speakText(welcomeMessage)
        }
        setTranscript([{
          id: 0,
          type: 'ai',
          text: welcomeMessage,
          timestamp: new Date()
        }])
      }, 1000)

    } catch (err: any) {
      setError(err.message || 'Failed to start voice chat')
      endCall()
    }
  }

  const endCall = () => {
    if (recognitionRef.current) {
      recognitionRef.current.stop()
      recognitionRef.current = null
    }
    if (window.speechSynthesis) {
      window.speechSynthesis.cancel()
    }
    disconnectWebSocket()
    audioQueueRef.current = []
    isPlayingRef.current = false
    isSpeakingRef.current = false
    setIsCallActive(false)
    setIsListening(false)
    setIsSpeaking(false)
  }

  const toggleMute = () => {
    if (isMuted && recognitionRef.current) {
      try {
        recognitionRef.current.start()
        setIsMuted(false)
      } catch (e) {
        console.error('Failed to resume recognition')
      }
    } else if (recognitionRef.current) {
      recognitionRef.current.stop()
      setIsMuted(true)
      setIsListening(false)
    }
  }

  const toggleSpeech = () => {
    sendInterrupt()
  }

  const quickPrompts = [
    "What's my CGPA?",
    "Show available books",
    "Shuttle schedule?",
    "Help with resume"
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

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

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
                  <Typography sx={{ mb: 2, fontSize: '22px', fontWeight: 500, color: colors.onSurface }}>
                    Start a Live Voice Conversation
                  </Typography>
                  <Typography sx={{ color: colors.onSurfaceVariant, fontSize: '14px', mb: 3 }}>
                    Connect with DI's AI using voice. Get instant responses in real-time.
                  </Typography>

                  <Button 
                    variant="outlined"
                    startIcon={<Settings />}
                    onClick={() => setShowSettings(!showSettings)}
                    sx={{ 
                      mb: 2,
                      color: colors.onSurfaceVariant,
                      borderColor: colors.onSurfaceVariant,
                      borderRadius: '16px',
                      textTransform: 'none',
                    }}
                  >
                    Settings
                  </Button>

                  {showSettings && (
                    <Box sx={{ mb: 3 }}>
                      <FormControl size="small" sx={{ minWidth: 150, mr: 2 }}>
                        <InputLabel sx={{ color: colors.onSurfaceVariant }}>Language</InputLabel>
                        <Select
                          value={selectedLanguage}
                          label="Language"
                          onChange={(e) => setSelectedLanguage(e.target.value)}
                          sx={{ 
                            color: colors.onSurface,
                            '.MuiOutlinedInput-notchedOutline': { borderColor: colors.onSurfaceVariant }
                          }}
                        >
                          <MenuItem value="en-US">English</MenuItem>
                          <MenuItem value="bn-BD">Bangla</MenuItem>
                        </Select>
                      </FormControl>
                      <FormControl size="small" sx={{ minWidth: 150 }}>
                        <InputLabel sx={{ color: colors.onSurfaceVariant }}>Audio Mode</InputLabel>
                        <Select
                          value={useWebSocket ? 'streaming' : 'standard'}
                          label="Audio Mode"
                          onChange={(e) => setUseWebSocket(e.target.value === 'streaming')}
                          sx={{ 
                            color: colors.onSurface,
                            '.MuiOutlinedInput-notchedOutline': { borderColor: colors.onSurfaceVariant }
                          }}
                        >
                          <MenuItem value="streaming">Streaming (Fast)</MenuItem>
                          <MenuItem value="standard">Standard</MenuItem>
                        </Select>
                      </FormControl>
                    </Box>
                  )}

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
                    flexDirection: 'column',
                    alignItems: 'center', 
                    justifyContent: 'center', 
                    bgcolor: '#0e0e0f', 
                    borderRadius: '16px', 
                    mb: 2,
                    p: 3
                  }}>
                    <Box sx={{ 
                      width: 120, 
                      height: 120, 
                      borderRadius: '50%', 
                      bgcolor: isSpeaking ? 'rgba(76, 175, 80, 0.2)' : isListening ? 'rgba(138, 180, 248, 0.2)' : 'rgba(138, 180, 248, 0.1)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      mb: 2,
                      border: `3px solid ${isSpeaking ? colors.success : isListening ? colors.primary : colors.onSurfaceVariant}`,
                      animation: isSpeaking ? 'bounce 0.5s infinite' : isListening ? 'pulse 1.5s infinite' : 'none',
                      transition: 'all 0.3s ease'
                    }}>
                      {isSpeaking ? (
                        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#4caf50" strokeWidth="2">
                          <path d="M11 5L6 9H2v6h4l5 4V5z" />
                          <path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07" />
                        </svg>
                      ) : isListening ? (
                        <Mic sx={{ fontSize: 48, color: colors.primary }} />
                      ) : (
                        <Videocam sx={{ fontSize: 48, color: colors.success }} />
                      )}
                    </Box>

                    <Typography sx={{ color: colors.onSurfaceVariant, fontSize: '16px', mb: 1 }}>
                      {isSpeaking ? 'Speaking...' : isListening ? 'Listening...' : 'Ready'}
                    </Typography>
                  </Box>

                  <Box sx={{ display: 'flex', justifyContent: 'center', gap: 2, mb: 2 }}>
                    <IconButton 
                      onClick={toggleMute} 
                      sx={{ 
                        bgcolor: isMuted ? colors.error : '#444746', 
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
                      onClick={toggleSpeech}
                      sx={{ 
                        bgcolor: '#444746', 
                        color: 'white',
                        borderRadius: '28px',
                        width: 52,
                        height: 52,
                        '&:hover': { bgcolor: '#555b67' }
                      }}
                    >
                      {isSpeaking ? <StopCircle /> : <PlayArrow />}
                    </IconButton>

                    <IconButton 
                      onClick={endCall} 
                      sx={{ 
                        bgcolor: colors.error, 
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
                        onClick={() => isCallActive && processUserSpeech(p)}
                        sx={{ 
                          cursor: 'pointer',
                          bgcolor: 'rgba(138, 180, 248, 0.12)',
                          color: colors.primary,
                          borderRadius: '9999px',
                          fontSize: '12px',
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
            <CardContent sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
              <Typography sx={{ mb: 2, fontSize: '16px', fontWeight: 500, color: colors.onSurface }}>
                Transcript
              </Typography>
              
              <Box sx={{ flexGrow: 1, overflow: 'auto' }}>
                <List>
                  {transcript.length === 0 ? (
                    <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
                      <Mic sx={{ fontSize: 48, color: colors.onSurfaceVariant, mb: 2, opacity: 0.5 }} />
                      <Typography sx={{ color: colors.onSurfaceVariant, textAlign: 'center', fontSize: '14px' }}>
                        Start talking to see your conversation
                      </Typography>
                    </Box>
                  ) : (
                    transcript.map((item) => (
                      <ListItem key={item.id} sx={{ 
                        bgcolor: item.type === 'ai' ? 'rgba(138, 180, 248, 0.1)' : '#2a2a2b', 
                        borderRadius: '16px', 
                        mb: 1,
                        flexDirection: 'column',
                        alignItems: 'flex-start'
                      }}>
                        <Typography sx={{ fontSize: '10px', color: colors.onSurfaceVariant, mb: 0.5 }}>
                          {item.type === 'ai' ? 'AI' : 'You'} • {item.timestamp.toLocaleTimeString()}
                        </Typography>
                        <ListItemText 
                          primary={item.text}
                          primaryTypographyProps={{
                            sx: { color: colors.onSurface, fontSize: '14px' }
                          }}
                        />
                      </ListItem>
                    ))
                  )}
                </List>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <style>{`
        @keyframes pulse {
          0%, 100% { transform: scale(1); }
          50% { transform: scale(1.05); }
        }
        @keyframes bounce {
          0%, 100% { transform: scale(1); }
          50% { transform: scale(1.03); }
        }
      `}</style>
    </Box>
  )
}