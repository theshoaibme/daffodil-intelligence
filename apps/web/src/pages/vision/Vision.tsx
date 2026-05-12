import React, { useState, useRef } from 'react'
import { Box, Typography, Button, Card, CardContent, Grid } from '@mui/material'
import { api } from '../../services/api'

const colors = {
  surface: '#131314',
  onSurface: '#e5e2e3',
  onSurfaceVariant: '#c3c6d1',
  primary: '#8ab4f8',
  primaryContainer: '#8ab4f8',
}

const Vision: React.FC = () => {
  const [isStreaming, setIsStreaming] = useState(false)
  const [analysis, setAnalysis] = useState<string>('')
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [capturedImage, setCapturedImage] = useState<string | null>(null)
  const videoRef = useRef<HTMLVideoElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const streamRef = useRef<MediaStream | null>(null)

  const startCamera = async () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop())
    }
    
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment', width: 1280, height: 720 }
      })
      streamRef.current = stream
      if (videoRef.current) {
        videoRef.current.srcObject = stream
        videoRef.current.play()
        setIsStreaming(true)
      }
    } catch (err) {
      console.error('Camera error:', err)
    }
  }

  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop())
      streamRef.current = null
    }
    setIsStreaming(false)
  }

  const captureAndAnalyze = async () => {
    if (!videoRef.current || !canvasRef.current) return
    
    const video = videoRef.current
    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')
    
    if (!ctx) {
      setAnalysis('Error: Could not initialize canvas context')
      return
    }
    
    canvas.width = video.videoWidth
    canvas.height = video.videoHeight
    ctx.drawImage(video, 0, 0)
    
    const imageData = canvas.toDataURL('image/jpeg', 0.8)
    setCapturedImage(imageData)
    setIsAnalyzing(true)
    
    try {
      const response = await fetch(`${api.getBaseUrl()}/api/agents/vision/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ image: imageData.split(',')[1] })
      })
      
      if (response.ok) {
        const data = await response.json()
        if (data.error) {
          setAnalysis(`Analysis error: ${data.error}`)
        } else {
          setAnalysis(data.analysis || 'Analysis complete')
        }
      } else {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }))
        setAnalysis(`Server error: ${errorData.detail || response.statusText}`)
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error'
      setAnalysis(`Network error: ${errorMessage}`)
    } finally {
      setIsAnalyzing(false)
    }
  }

  return (
    <Box sx={{ p: { xs: 2, md: 3 }, maxWidth: 900, mx: 'auto' }}>
      <Box sx={{ textAlign: 'center', mb: 3 }}>
        <Typography sx={{ 
          mb: 1, 
          fontSize: '28px',
          fontWeight: 500,
          color: colors.primary,
          fontFamily: '"Roboto Flex", Roboto, sans-serif'
        }}>
          Real-Time Vision Camera
        </Typography>
        <Typography sx={{ 
          color: colors.onSurfaceVariant,
          fontFamily: '"Roboto Flex", Roboto, sans-serif',
          fontSize: '14px'
        }}>
          Point your camera at objects, documents, or text for AI analysis
        </Typography>
      </Box>

      <Card sx={{ 
        bgcolor: '#191A1F', 
        border: '1px solid #444746',
        borderRadius: '28px',
        overflow: 'hidden',
        mb: 3
      }}>
        <Box sx={{ 
          position: 'relative',
          aspectRatio: '16/9',
          bgcolor: '#0e0e0f',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center'
        }}>
          <video 
            ref={videoRef}
            playsInline
            muted
            style={{ 
              display: isStreaming ? 'block' : 'none',
              width: '100%',
              height: '100%',
              objectFit: 'cover'
            }}
          />
          
          {!isStreaming && !capturedImage && (
            <Box sx={{ textAlign: 'center', color: colors.onSurfaceVariant }}>
              <Typography sx={{ fontSize: '64px', mb: 2 }}>📷</Typography>
              <Typography sx={{ fontFamily: '"Roboto Flex", Roboto, sans-serif', fontSize: '14px' }}>
                Click "Start Camera" to begin
              </Typography>
            </Box>
          )}
          
          {capturedImage && (
            <img 
              src={capturedImage} 
              alt="Captured" 
              style={{ 
                width: '100%', 
                height: '100%', 
                objectFit: 'cover' 
              }} 
            />
          )}
          
          <canvas ref={canvasRef} style={{ display: 'none' }} />
          
          {isStreaming && (
            <Box sx={{ 
              position: 'absolute',
              top: 16,
              left: 16,
              bgcolor: '#ef4444',
              color: 'white',
              px: 2,
              py: 0.75,
              borderRadius: '9999px',
              display: 'flex',
              alignItems: 'center',
              gap: 1,
              fontWeight: 600,
              fontSize: '12px',
              fontFamily: '"Roboto Flex", Roboto, sans-serif'
            }}>
              <Box sx={{ 
                width: 8, 
                height: 8, 
                bgcolor: 'white', 
                borderRadius: '50%',
                animation: 'pulse 1s infinite'
              }} />
              LIVE
            </Box>
          )}
        </Box>
      </Card>

      <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', mb: 3 }}>
        {!isStreaming ? (
          <Button 
            variant="contained"
            onClick={startCamera}
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
            Start Camera
          </Button>
        ) : (
          <>
            <Button 
              variant="contained"
              onClick={captureAndAnalyze}
              disabled={isAnalyzing}
              sx={{
                bgcolor: '#22c55e',
                color: 'white',
                borderRadius: '16px',
                px: 3,
                py: 1.5,
                fontWeight: 500,
                fontSize: '14px',
                fontFamily: '"Roboto Flex", Roboto, sans-serif',
                textTransform: 'none',
                '&:hover': { bgcolor: '#16a34a' },
                '&:disabled': { bgcolor: '#444746', color: '#8d919b' }
              }}
            >
              {isAnalyzing ? 'Analyzing...' : 'Capture & Analyze'}
            </Button>
            <Button 
              variant="contained"
              onClick={stopCamera}
              sx={{
                bgcolor: '#ef4444',
                color: 'white',
                borderRadius: '16px',
                px: 3,
                py: 1.5,
                fontWeight: 500,
                fontSize: '14px',
                fontFamily: '"Roboto Flex", Roboto, sans-serif',
                textTransform: 'none',
                '&:hover': { bgcolor: '#dc2626' }
              }}
            >
              Stop
            </Button>
          </>
        )}
      </Box>

      {analysis && (
        <Card sx={{ 
          bgcolor: '#191A1F', 
          border: '1px solid #444746',
          borderRadius: '24px',
          mb: 3
        }}>
          <CardContent>
            <Typography sx={{ 
              mb: 2,
              fontSize: '16px',
              fontWeight: 500,
              color: colors.primary,
              fontFamily: '"Roboto Flex", Roboto, sans-serif'
            }}>
              AI Analysis Result
            </Typography>
            <Typography sx={{ 
              color: colors.onSurface,
              fontFamily: '"Roboto Flex", Roboto, sans-serif',
              fontSize: '14px',
              mb: 2
            }}>
              {analysis}
            </Typography>
            <Box sx={{ display: 'flex', gap: 1 }}>
              {['Objects', 'Text', 'Scene'].map((tag) => (
                <Box key={tag} sx={{
                  bgcolor: 'rgba(138, 180, 248, 0.12)',
                  color: colors.primary,
                  px: 2,
                  py: 0.5,
                  borderRadius: '9999px',
                  fontSize: '12px',
                  fontFamily: '"Roboto Flex", Roboto, sans-serif'
                }}>
                  {tag}
                </Box>
              ))}
            </Box>
          </CardContent>
        </Card>
      )}

      <Typography sx={{ 
        mb: 2,
        fontSize: '16px',
        fontWeight: 500,
        color: colors.onSurface,
        fontFamily: '"Roboto Flex", Roboto, sans-serif'
      }}>
        Features
      </Typography>

      <Grid container spacing={2}>
        {[
          { icon: '🔴', title: 'Object Detection', desc: 'Identifies objects in real-time' },
          { icon: '📝', title: 'Text Recognition', desc: 'Extracts text from images (OCR)' },
          { icon: '🏷️', title: 'Scene Classification', desc: 'Identifies environment/context' },
          { icon: '📊', title: 'Chart Analysis', desc: 'Reads graphs and tables' }
        ].map((feature, i) => (
          <Grid item xs={12} sm={6} key={i}>
            <Card sx={{ 
              bgcolor: '#191A1F', 
              border: '1px solid #444746',
              borderRadius: '24px',
              p: 2
            }}>
              <Typography sx={{ fontSize: '24px', mb: 1 }}>{feature.icon}</Typography>
              <Typography sx={{ 
                fontWeight: 500,
                color: colors.onSurface,
                fontFamily: '"Roboto Flex", Roboto, sans-serif',
                fontSize: '14px',
                mb: 0.5
              }}>
                {feature.title}
              </Typography>
              <Typography sx={{ 
                color: colors.onSurfaceVariant,
                fontFamily: '"Roboto Flex", Roboto, sans-serif',
                fontSize: '12px'
              }}>
                {feature.desc}
              </Typography>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  )
}

export default Vision