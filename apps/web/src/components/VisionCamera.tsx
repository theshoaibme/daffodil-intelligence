import React, { useRef, useState, useEffect } from 'react';
import { api } from '../services/api';

interface VisionCameraProps {
  onFrameCapture?: (frame: string) => void;
}

const VisionCamera: React.FC<VisionCameraProps> = ({ 
  onFrameCapture
}) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [analysis, setAnalysis] = useState<string>('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string>('');

  useEffect(() => {
    return () => {
      stopCamera();
    };
  }, []);

  const startCamera = async () => {
    if (stream) {
      stream.getTracks().forEach(track => track.stop())
    }
    
    try {
      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: 'environment',
          width: { ideal: 1920 },
          height: { ideal: 1080 }
        },
        audio: false
      });
      
      setStream(mediaStream);
      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream;
        await videoRef.current.play();
        setIsStreaming(true);
        setError('');
      }
    } catch (err) {
      setError(`Camera error: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  };

  const stopCamera = () => {
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
      setStream(null);
      setIsStreaming(false);
    }
  };

  const captureFrame = (): string | null => {
    if (!videoRef.current || !canvasRef.current) return null;
    
    const video = videoRef.current;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    
    if (!ctx) return null;
    
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    ctx.drawImage(video, 0, 0);
    
    return canvas.toDataURL('image/jpeg', 0.8).split(',')[1];
  };

  const analyzeFrame = async () => {
    const frameData = captureFrame();
    if (!frameData) return;
    
    setIsAnalyzing(true);
    
    try {
      const response = await fetch(`${api.getBaseUrl()}/api/agents/vision/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ image: frameData })
      });
      
      if (response.ok) {
        const data = await response.json();
        if (data.error) {
          setAnalysis(`Error: ${data.error}`);
        } else {
          setAnalysis(data.analysis || 'Analysis complete');
        }
      } else {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
        setAnalysis(`Server error: ${errorData.detail || response.statusText}`);
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setAnalysis(`Network error: ${errorMessage}`);
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="vision-camera">
      <div className="camera-container">
        <video 
          ref={videoRef}
          className="camera-video"
          playsInline
          muted
          style={{ display: isStreaming ? 'block' : 'none' }}
        />
        
        {!isStreaming && (
          <div className="camera-placeholder">
            {error ? (
              <div className="camera-error">
                <span className="error-icon">⚠️</span>
                <p>{error}</p>
                <button onClick={startCamera}>Try Again</button>
              </div>
            ) : (
              <div className="camera-start">
                <span className="camera-icon">📷</span>
                <p>Click to start camera</p>
              </div>
            )}
          </div>
        )}
        
        <canvas ref={canvasRef} style={{ display: 'none' }} />
        
        {isStreaming && (
          <div className="camera-overlay">
            <div className="overlay-top">
              <span className="recording-indicator">● LIVE</span>
              <span className="fps-counter">30 FPS</span>
            </div>
            
            {analysis && (
              <div className="analysis-result">
                <span className="analysis-label">AI Analysis:</span>
                <p>{analysis}</p>
              </div>
            )}
            
            <div className="overlay-bottom">
              <button 
                className={`control-btn ${isAnalyzing ? 'analyzing' : ''}`}
                onClick={analyzeFrame}
                disabled={isAnalyzing}
              >
                {isAnalyzing ? '🔄 Analyzing...' : '📸 Analyze'}
              </button>
              
              <button 
                className="control-btn"
                onClick={() => {
                  const frame = captureFrame();
                  if (frame && onFrameCapture) {
                    onFrameCapture(frame);
                  }
                }}
              >
                📷 Snap
              </button>
            </div>
          </div>
        )}
      </div>
      
      <div className="camera-controls">
        <button onClick={startCamera} disabled={isStreaming}>Start</button>
        <button onClick={stopCamera} disabled={!isStreaming}>Stop</button>
      </div>
    </div>
  );
};

export default VisionCamera;