import { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { 
  ArrowLeft, 
  Mic, 
  MicOff, 
  PhoneOff, 
  Settings, 
  Volume2, 
  VolumeX, 
  Languages, 
  Cpu, 
  AlertTriangle,
  Sparkles,
  MessageSquare
} from "lucide-react";

interface TranscriptItem {
  id: number;
  type: 'user' | 'ai';
  text: string;
  timestamp: Date;
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
];

const FILLERS_BN = [
  "হুম, ",
  "চিন্তা করি... ",
  "ঠিক আছে, ",
  "তাহলে, ",
  "আচ্ছা, ",
  "একটু দেখি... ",
  "অবশ্যই! ",
  "চমৎকার প্রশ্ন! ",
];

const selectBestVoice = (lang: string): SpeechSynthesisVoice | null => {
  if (!window.speechSynthesis) return null;
  const voices = window.speechSynthesis.getVoices();
  const langPrefix = lang.split('-')[0];
  
  const preferred = voices.find(v => 
    v.lang.startsWith(langPrefix) && (v.localService || v.name.includes('Premium') || v.name.includes('Neural'))
  );
  return preferred || voices.find(v => v.lang.startsWith(langPrefix)) || null;
};

const addFiller = (text: string, lang: string): string => {
  if (!text.trim()) return text;
  
  const fillers = lang.startsWith('bn') ? FILLERS_BN : FILLERS_EN;
  const isQuestion = text.trim().endsWith('?');
  const isGreeting = /^(hi|hello|hey|হ্যালো|হাই|নমস্কার)/i.test(text.trim());
  
  if (!isQuestion && !isGreeting && Math.random() < 0.35) {
    const filler = fillers[Math.floor(Math.random() * fillers.length)];
    return filler + text;
  }
  return text;
};

const preprocessText = (text: string): string => {
  let processed = text
    .replace(/\s+/g, ' ')
    .replace(/([.!?]){2,}/g, '$1')
    .replace(/,+/g, ',');
  
  if (processed.length < 30) {
    processed = processed.charAt(0).toUpperCase() + processed.slice(1);
  }
  
  return processed;
};

const getApiUrl = () => import.meta.env.VITE_API_URL || 'http://localhost:8000';
const getWsUrl = () => {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  return import.meta.env.VITE_WS_URL || `${protocol}//${window.location.hostname}:8000`;
};

const Bar = ({ delay, active, colorClass }: { delay: number; active: boolean; colorClass: string }) => (
  <motion.div
    animate={active ? {
      scaleY: [1, 2.8, 1],
    } : {
      scaleY: 1
    }}
    transition={active ? {
      duration: 1.2,
      repeat: Infinity,
      delay: delay,
      ease: "easeInOut"
    } : {}}
    className={`w-1.5 h-6 ${colorClass} rounded-full origin-center`}
  />
);

export function LiveVoicePage() {
  const navigate = useNavigate();
  const [isMuted, setIsMuted] = useState(false);
  const [isCallActive, setIsCallActive] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [transcript, setTranscript] = useState<TranscriptItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [showSettings, setShowSettings] = useState(false);
  const [selectedLanguage, setSelectedLanguage] = useState('en-US');
  const [useWebSocket, setUseWebSocket] = useState(true);
  const [voiceModel, setVoiceModel] = useState('Aoede');
  const [isSpeechSupported, setIsSpeechSupported] = useState(true);

  const recognitionRef = useRef<any>(null);
  const transcriptIdRef = useRef(0);
  const isSpeakingRef = useRef(false);
  const wsRef = useRef<WebSocket | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const audioQueueRef = useRef<AudioBuffer[]>([]);
  const isPlayingRef = useRef(false);
  const transcriptEndRef = useRef<HTMLDivElement>(null);

  // Check speech synthesis & recognition support
  useEffect(() => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setIsSpeechSupported(false);
    }

    const loadVoices = () => {
      if (window.speechSynthesis) {
        window.speechSynthesis.getVoices();
      }
    };
    
    loadVoices();
    if (window.speechSynthesis) {
      window.speechSynthesis.onvoiceschanged = loadVoices;
    }

    return () => {
      cleanupCallResources();
    };
  }, []);

  // Auto-scroll transcript
  useEffect(() => {
    transcriptEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [transcript]);

  const cleanupCallResources = () => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
      recognitionRef.current = null;
    }
    if (window.speechSynthesis) {
      window.speechSynthesis.cancel();
    }
    if (wsRef.current) {
      disconnectWebSocket();
    }
    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }
  };

  const initAudioContext = () => {
    if (!audioContextRef.current) {
      audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)();
    }
    if (audioContextRef.current.state === 'suspended') {
      audioContextRef.current.resume();
    }
    return audioContextRef.current;
  };

  const configureTTS = async (modelName: string) => {
    try {
      const url = `${getApiUrl()}/api/voice/tts/config`;
      await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ voice_id: modelName })
      });
    } catch (err) {
      console.error('Failed to configure TTS voice model:', err);
    }
  };

  const playAudioChunk = async (base64Audio: string) => {
    try {
      const audioContext = initAudioContext();
      
      const binaryString = atob(base64Audio);
      const bytes = new Uint8Array(binaryString.length);
      for (let i = 0; i < binaryString.length; i++) {
        bytes[i] = binaryString.charCodeAt(i);
      }
      
      const audioBuffer = await audioContext.decodeAudioData(bytes.buffer);
      audioQueueRef.current.push(audioBuffer);
      
      if (!isPlayingRef.current) {
        playNextAudio();
      }
    } catch (err) {
      console.error('Error playing audio chunk:', err);
    }
  };

  const playNextAudio = () => {
    if (audioQueueRef.current.length === 0) {
      isPlayingRef.current = false;
      isSpeakingRef.current = false;
      setIsSpeaking(false);
      return;
    }

    isPlayingRef.current = true;
    const audioContext = audioContextRef.current;
    if (!audioContext) return;

    const buffer = audioQueueRef.current.shift();
    if (!buffer) {
      playNextAudio();
      return;
    }

    const source = audioContext.createBufferSource();
    source.buffer = buffer;
    source.connect(audioContext.destination);
    
    source.onended = () => {
      if (audioQueueRef.current.length > 0) {
        playNextAudio();
      } else {
        isPlayingRef.current = false;
        isSpeakingRef.current = false;
        setIsSpeaking(false);
      }
    };

    source.start(0);
  };

  const connectWebSocket = (userId: number = 1) => {
    return new Promise<void>((resolve, reject) => {
      const wsUrl = `${getWsUrl()}/voice/ws/${userId}`;
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('Voice WebSocket connected');
        resolve();
      };

      ws.onmessage = async (event) => {
        const data = JSON.parse(event.data);
        
        if (data.type === 'connected') {
          console.log('Voice session connected:', data.session);
        } else if (data.type === 'audio_chunk') {
          if (data.audio) {
            isSpeakingRef.current = true;
            setIsSpeaking(true);
            await playAudioChunk(data.audio);
          }
          if (data.text) {
            // Realtime streaming transcription from AI
            appendOrUpdateTranscript(data.text, 'ai');
          }
        } else if (data.type === 'response_text' && data.text) {
          appendOrUpdateTranscript(data.text, 'ai');
        } else if (data.type === 'complete') {
          isSpeakingRef.current = false;
          setIsSpeaking(false);
        } else if (data.type === 'interrupted') {
          audioQueueRef.current = [];
          isPlayingRef.current = false;
          isSpeakingRef.current = false;
          setIsSpeaking(false);
        } else if (data.type === 'interrupt_ack') {
          console.log('AI voice interrupted');
        } else if (data.type === 'error') {
          console.error('WebSocket error:', data.message);
          setError(data.message);
        }
      };

      ws.onerror = (err) => {
        console.error('WebSocket connection error:', err);
        reject(err);
      };

      ws.onclose = () => {
        console.log('Voice WebSocket closed');
        wsRef.current = null;
      };
    });
  };

  const appendOrUpdateTranscript = (text: string, type: 'user' | 'ai') => {
    if (!text.trim()) return;
    setTranscript(prev => {
      // Avoid duplicate AI streaming entries
      const last = prev[prev.length - 1];
      if (last && last.type === type && type === 'ai') {
        // If it starts with the last sentence, just replace or append
        return [...prev.slice(0, -1), { ...last, text, timestamp: new Date() }];
      }
      return [...prev, { id: transcriptIdRef.current++, type, text, timestamp: new Date() }];
    });
  };

  const sendInterrupt = () => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'interrupt' }));
      audioQueueRef.current = [];
      isPlayingRef.current = false;
    }
    if (window.speechSynthesis) {
      window.speechSynthesis.cancel();
    }
    isSpeakingRef.current = false;
    setIsSpeaking(false);
  };

  const sendTextMessage = async (text: string) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'text',
        data: text,
        language: selectedLanguage.split('-')[0]
      }));
    }
  };

  const disconnectWebSocket = () => {
    if (wsRef.current) {
      try {
        wsRef.current.send(JSON.stringify({ type: 'end' }));
      } catch {}
      wsRef.current.close();
      wsRef.current = null;
    }
    audioQueueRef.current = [];
    isPlayingRef.current = false;
  };

  const requestMicrophonePermission = async (): Promise<boolean> => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      stream.getTracks().forEach(track => track.stop());
      return true;
    } catch (err) {
      console.error('Microphone permission denied:', err);
      return false;
    }
  };

  const initSpeechRecognition = async () => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    
    if (!SpeechRecognition) {
      setError('Speech recognition is not supported in this browser. Please try Chrome or Edge.');
      return false;
    }

    const hasPermission = await requestMicrophonePermission();
    if (!hasPermission) {
      setError('Microphone access denied. Please grant microphone access and try again.');
      return false;
    }

    recognitionRef.current = new SpeechRecognition();
    recognitionRef.current.continuous = true;
    recognitionRef.current.interimResults = true;
    recognitionRef.current.lang = selectedLanguage;

    recognitionRef.current.onstart = () => {
      setIsListening(true);
      setError(null);
    };

    recognitionRef.current.onresult = async (event: any) => {
      sendInterrupt();
      
      const result = event.results[event.results.length - 1];
      const transcriptText = result[0].transcript.trim();

      if (result.isFinal && transcriptText) {
        await processUserSpeech(transcriptText);
      }
    };

    recognitionRef.current.onerror = (event: any) => {
      console.error('Speech recognition error:', event.error);
      
      if (event.error === 'not-allowed') {
        setError('Microphone access denied. Please allow microphone access in your browser settings.');
      } else if (event.error === 'security') {
        setError('Speech recognition requires a secure connection (HTTPS or localhost).');
      } else if (event.error !== 'aborted' && event.error !== 'no-speech') {
        setError(`Speech recognition error: ${event.error}`);
      }
    };

    recognitionRef.current.onend = () => {
      if (isCallActive && !isMuted && recognitionRef.current) {
        try {
          recognitionRef.current.start();
        } catch (e) {
          console.log('Recognition restart failed');
        }
      }
    };

    return true;
  };

  const processUserSpeech = async (text: string) => {
    if (!text.trim()) return;

    appendOrUpdateTranscript(text, 'user');

    try {
      if (useWebSocket && wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        isSpeakingRef.current = true;
        setIsSpeaking(true);
        await sendTextMessage(text);
      } else {
        setIsSpeaking(true);
        isSpeakingRef.current = true;
        
        const response = await fetch(`${getApiUrl()}/api/agents/gemini/chat/simple`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: text })
        });

        const data = await response.json();
        let aiResponse = data.response || data.error || 'Sorry, I could not process that request.';
        
        aiResponse = preprocessText(aiResponse);
        aiResponse = addFiller(aiResponse, selectedLanguage);

        appendOrUpdateTranscript(aiResponse, 'ai');
        speakText(aiResponse);
      }
    } catch (err) {
      console.error('Failed to process speech input:', err);
      const errorResponse = preprocessText('Sorry, I encountered an error. Please try again.');
      appendOrUpdateTranscript(errorResponse, 'ai');
    }
  };

  const speakText = (text: string) => {
    if (!window.speechSynthesis) return;

    window.speechSynthesis.cancel();

    const sentences = text.match(/[^.!?।]+[.!?।]+/g) || [text];
    const voice = selectBestVoice(selectedLanguage);
    const baseRate = text.length > 200 ? 1.1 : 1.05;
    const basePitch = 1.02;

    let completedCount = 0;
    const totalSentences = sentences.length;

    sentences.forEach((sentence, index) => {
      const cleanSentence = sentence.trim();
      if (!cleanSentence) return;

      setTimeout(() => {
        if (!isSpeakingRef.current && index > 0) return;

        const utterance = new SpeechSynthesisUtterance(cleanSentence);
        utterance.lang = selectedLanguage;
        
        const wordCount = cleanSentence.split(/\s+/).length;
        const rate = wordCount < 5 ? baseRate + 0.05 : (wordCount > 20 ? baseRate - 0.05 : baseRate);
        utterance.rate = rate;
        utterance.pitch = basePitch;
        utterance.volume = 1.0;
        
        if (voice) {
          utterance.voice = voice;
        }

        utterance.onstart = () => {
          isSpeakingRef.current = true;
          setIsSpeaking(true);
        };
        
        utterance.onend = () => {
          completedCount++;
          if (completedCount >= totalSentences) {
            isSpeakingRef.current = false;
            setIsSpeaking(false);
          }
        };
        
        utterance.onerror = () => {
          completedCount++;
          if (completedCount >= totalSentences) {
            isSpeakingRef.current = false;
            setIsSpeaking(false);
          }
        };

        window.speechSynthesis.speak(utterance);
      }, index * 100);
    });
  };

  const startCall = async () => {
    try {
      setError(null);
      setTranscript([]);

      const initialized = await initSpeechRecognition();
      if (!initialized) return;

      // Make sure backend has the correct voice config loaded
      await configureTTS(voiceModel);

      setIsCallActive(true);

      if (useWebSocket) {
        try {
          await connectWebSocket(1);
        } catch (wsErr) {
          console.warn('WebSocket connection failed, using HTTP fallback:', wsErr);
        }
      }

      setTimeout(() => {
        if (recognitionRef.current) {
          try {
            recognitionRef.current.start();
          } catch (e) {
            console.error('Failed to start recognition:', e);
          }
        }
      }, 500);

      const welcomeMessage = selectedLanguage.startsWith('bn') 
        ? "হ্যালো! আমি আপনার এআই সহকারী। আজ আপনাকে কীভাবে সাহায্য করতে পারি?"
        : "Hello! I'm your AI assistant. How can I help you today?";
      
      setTimeout(() => {
        if (useWebSocket && wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
          sendTextMessage(welcomeMessage);
        } else {
          speakText(welcomeMessage);
        }
        setTranscript([{
          id: 0,
          type: 'ai',
          text: welcomeMessage,
          timestamp: new Date()
        }]);
      }, 1000);

    } catch (err: any) {
      setError(err.message || 'Failed to start voice chat');
      endCall();
    }
  };

  const endCall = () => {
    cleanupCallResources();
    setIsCallActive(false);
    setIsListening(false);
    setIsSpeaking(false);
    setIsMuted(false);
  };

  const toggleMute = () => {
    if (isMuted && recognitionRef.current) {
      try {
        recognitionRef.current.start();
        setIsMuted(false);
      } catch (e) {
        console.error('Failed to resume recognition');
      }
    } else if (recognitionRef.current) {
      recognitionRef.current.stop();
      setIsMuted(true);
      setIsListening(false);
    }
  };

  const quickPrompts = selectedLanguage.startsWith('bn') ? [
    "আমার সিজিপিএ কত?",
    "কী কী বই পাওয়া যাবে?",
    "শাটল বাস এর শিডিউল?",
    "রেজুমে তৈরিতে সাহায্য করুন"
  ] : [
    "What's my CGPA?",
    "Show available books",
    "Shuttle schedule?",
    "Help with resume"
  ];

  return (
    <div className="min-h-screen bg-background dot-pattern text-on-surface flex flex-col font-sans">
      {/* Top Header */}
      <header className="px-6 py-4 flex items-center justify-between border-b border-outline-variant/20 bg-surface-container-lowest/80 backdrop-blur-md sticky top-0 z-40">
        <div className="flex items-center gap-4">
          <button 
            onClick={() => navigate("/")}
            className="p-2 rounded-full hover:bg-surface-container-high text-on-surface-variant hover:text-on-surface transition-all cursor-pointer border-0 outline-none"
          >
            <ArrowLeft size={20} />
          </button>
          <div>
            <h1 className="text-xl font-semibold tracking-tight">Live Voice Agent</h1>
            <p className="text-xs text-on-surface-variant">Real-time voice and streaming assistant</p>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-6 grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        {/* Left Side: Call Hub Card */}
        <div className="lg:col-span-7 flex flex-col gap-6">
          <motion.div 
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-surface-container-low border border-outline-variant/30 rounded-3xl p-6 shadow-sm flex flex-col items-center justify-center min-h-[500px]"
          >
            {!isCallActive ? (
              <div className="text-center max-w-md flex flex-col items-center">
                {/* Visual Circle (Inactive) */}
                <div className="w-32 h-32 rounded-full bg-primary/10 text-primary flex items-center justify-center mb-6">
                  <Mic size={56} className="animate-pulse" />
                </div>
                
                <h2 className="text-2xl font-medium mb-2">Voice Call Workspace</h2>
                <p className="text-sm text-on-surface-variant mb-6">
                  Experience instantaneous, low-latency spoken responses with DI's AI Orchestrator. 
                </p>

                {/* Settings Panel Toggle */}
                <button
                  onClick={() => setShowSettings(!showSettings)}
                  className="flex items-center gap-2 px-4 py-2 border border-outline-variant/40 rounded-full hover:bg-primary/5 text-sm font-medium text-on-surface-variant hover:text-on-surface transition-all mb-6 cursor-pointer"
                >
                  <Settings size={16} />
                  <span>Configure Settings</span>
                </button>

                {/* Settings Panel Content */}
                <AnimatePresence>
                  {showSettings && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: "auto" }}
                      exit={{ opacity: 0, height: 0 }}
                      className="w-full grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6 text-left"
                    >
                      <div className="flex flex-col gap-1.5">
                        <label className="text-xs font-semibold text-on-surface-variant flex items-center gap-1">
                          <Languages size={13} />
                          Language
                        </label>
                        <select
                          value={selectedLanguage}
                          onChange={(e) => setSelectedLanguage(e.target.value)}
                          className="bg-surface-container-high border border-outline-variant/30 rounded-xl px-3 py-2 text-xs text-on-surface focus:ring-2 focus:ring-primary outline-none transition-all cursor-pointer"
                        >
                          <option value="en-US">English (US)</option>
                          <option value="bn-BD">বাংলা (Bangladesh)</option>
                        </select>
                      </div>

                      <div className="flex flex-col gap-1.5">
                        <label className="text-xs font-semibold text-on-surface-variant flex items-center gap-1">
                          <Cpu size={13} />
                          Voice Model
                        </label>
                        <select
                          value={voiceModel}
                          onChange={(e) => setVoiceModel(e.target.value)}
                          className="bg-surface-container-high border border-outline-variant/30 rounded-xl px-3 py-2 text-xs text-on-surface focus:ring-2 focus:ring-primary outline-none transition-all cursor-pointer"
                        >
                          <option value="Aoede">Aoede</option>
                          <option value="Puck">Puck</option>
                          <option value="Charon">Charon</option>
                          <option value="Ernie">Ernie</option>
                          <option value="Fenrir">Fenrir</option>
                        </select>
                      </div>

                      <div className="flex flex-col gap-1.5">
                        <label className="text-xs font-semibold text-on-surface-variant flex items-center gap-1">
                          <Sparkles size={13} />
                          Connection Mode
                        </label>
                        <select
                          value={useWebSocket ? 'streaming' : 'standard'}
                          onChange={(e) => setUseWebSocket(e.target.value === 'streaming')}
                          className="bg-surface-container-high border border-outline-variant/30 rounded-xl px-3 py-2 text-xs text-on-surface focus:ring-2 focus:ring-primary outline-none transition-all cursor-pointer"
                        >
                          <option value="streaming">WebSocket Stream</option>
                          <option value="standard">HTTP Poll</option>
                        </select>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>

                {error && (
                  <div className="flex items-start gap-2 bg-error-container/10 border border-error/30 rounded-2xl p-4 mb-6 text-left max-w-sm">
                    <AlertTriangle className="text-error flex-shrink-0 mt-0.5" size={16} />
                    <p className="text-xs text-error font-medium">{error}</p>
                  </div>
                )}

                {/* Big Start Call Button */}
                <button
                  disabled={!isSpeechSupported}
                  onClick={startCall}
                  className={`flex items-center gap-2.5 px-8 py-3.5 rounded-full font-semibold text-sm transition-all shadow-md ${
                    isSpeechSupported 
                      ? "bg-primary text-on-primary hover:bg-primary-container cursor-pointer" 
                      : "bg-surface-container text-on-surface-variant/40 cursor-not-allowed"
                  }`}
                >
                  <Mic size={18} />
                  <span>Start Voice Chat</span>
                </button>
                
                {!isSpeechSupported && (
                  <p className="text-xs text-error mt-3 flex items-center gap-1.5">
                    <AlertTriangle size={13} />
                    Web Speech API is not fully supported in this browser.
                  </p>
                )}
              </div>
            ) : (
              <div className="w-full flex flex-col items-center justify-between h-[450px]">
                {/* Visualizer Circle (Active) */}
                <div className="relative flex items-center justify-center w-64 h-64 my-auto">
                  {/* Concentric expanding circles */}
                  <motion.div
                    animate={isSpeaking || isListening ? {
                      scale: [1, 1.3, 1],
                      opacity: [0.15, 0.05, 0.15]
                    } : {}}
                    transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
                    className={`absolute inset-0 rounded-full border-2 ${
                      isSpeaking ? 'border-emerald-500 bg-emerald-500/5' : 'border-primary bg-primary/5'
                    }`}
                  />
                  
                  <motion.div
                    animate={isSpeaking || isListening ? {
                      scale: [1, 1.5, 1],
                      opacity: [0.1, 0.02, 0.1]
                    } : {}}
                    transition={{ duration: 2.5, repeat: Infinity, ease: "easeInOut", delay: 0.5 }}
                    className={`absolute -inset-4 rounded-full border ${
                      isSpeaking ? 'border-emerald-500 bg-emerald-500/2' : 'border-primary bg-primary/2'
                    }`}
                  />

                  {/* Bubble Container */}
                  <motion.div
                    animate={{
                      scale: isSpeaking ? [1, 1.04, 1] : isListening ? [1, 1.02, 1] : 1
                    }}
                    transition={{ duration: 0.6, repeat: Infinity, ease: "easeInOut" }}
                    className={`relative w-44 h-44 rounded-full flex flex-col items-center justify-center border-4 shadow-xl transition-all duration-300 z-10 ${
                      isMuted
                        ? "bg-error/10 border-error text-error shadow-error/10"
                        : isSpeaking
                        ? "bg-emerald-500/10 border-emerald-500 text-emerald-500 shadow-emerald-500/10"
                        : isListening
                        ? "bg-primary/10 border-primary text-primary shadow-primary/10"
                        : "bg-surface-container border-outline-variant text-on-surface-variant"
                    }`}
                  >
                    <div className="flex flex-col items-center gap-2">
                      <div className="flex items-center justify-center gap-1 h-10">
                        <Bar delay={0.0} active={isSpeaking || isListening} colorClass={isSpeaking ? "bg-emerald-500" : isListening ? "bg-primary" : "bg-on-surface-variant/40"} />
                        <Bar delay={0.15} active={isSpeaking || isListening} colorClass={isSpeaking ? "bg-emerald-500" : isListening ? "bg-primary" : "bg-on-surface-variant/40"} />
                        <Bar delay={0.3} active={isSpeaking || isListening} colorClass={isSpeaking ? "bg-emerald-500" : isListening ? "bg-primary" : "bg-on-surface-variant/40"} />
                        <Bar delay={0.45} active={isSpeaking || isListening} colorClass={isSpeaking ? "bg-emerald-500" : isListening ? "bg-primary" : "bg-on-surface-variant/40"} />
                        <Bar delay={0.3} active={isSpeaking || isListening} colorClass={isSpeaking ? "bg-emerald-500" : isListening ? "bg-primary" : "bg-on-surface-variant/40"} />
                        <Bar delay={0.15} active={isSpeaking || isListening} colorClass={isSpeaking ? "bg-emerald-500" : isListening ? "bg-primary" : "bg-on-surface-variant/40"} />
                        <Bar delay={0.0} active={isSpeaking || isListening} colorClass={isSpeaking ? "bg-emerald-500" : isListening ? "bg-primary" : "bg-on-surface-variant/40"} />
                      </div>
                      <span className="text-[11px] font-bold uppercase tracking-widest">
                        {isMuted ? "Muted" : isSpeaking ? "Speaking" : isListening ? "Listening" : "Connected"}
                      </span>
                    </div>
                  </motion.div>
                </div>

                {/* Call Control Row */}
                <div className="flex items-center justify-center gap-4 mb-8">
                  {/* Mute Button */}
                  <button
                    onClick={toggleMute}
                    className={`p-4 rounded-full border transition-all cursor-pointer ${
                      isMuted 
                        ? "bg-error border-error text-white hover:bg-error-container" 
                        : "bg-surface-container-high border-outline-variant/30 text-on-surface hover:bg-surface-container-highest"
                    }`}
                    title={isMuted ? "Unmute Mic" : "Mute Mic"}
                  >
                    {isMuted ? <MicOff size={22} /> : <Mic size={22} />}
                  </button>

                  {/* Interrupt Voice / Speech control */}
                  <button
                    onClick={sendInterrupt}
                    className="p-4 rounded-full bg-surface-container-high border border-outline-variant/30 text-on-surface hover:bg-surface-container-highest transition-all cursor-pointer"
                    title="Stop AI Speech"
                  >
                    {isSpeaking ? <VolumeX size={22} /> : <Volume2 size={22} />}
                  </button>

                  {/* Disconnect/End Call Button */}
                  <button
                    onClick={endCall}
                    className="p-4 rounded-full bg-error text-white border-0 hover:bg-red-600 transition-all cursor-pointer shadow-lg shadow-error/20"
                    title="End Voice Call"
                  >
                    <PhoneOff size={22} />
                  </button>
                </div>

                {/* Quick Prompts */}
                <div className="flex flex-wrap items-center justify-center gap-2 w-full pt-4 border-t border-outline-variant/10">
                  {quickPrompts.map((promptText, i) => (
                    <button
                      key={i}
                      onClick={() => processUserSpeech(promptText)}
                      className="px-4 py-1.5 text-xs font-semibold text-primary bg-primary/10 border border-primary/25 rounded-full hover:bg-primary/20 transition-all cursor-pointer outline-none"
                    >
                      {promptText}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </motion.div>
        </div>

        {/* Right Side: Transcript Card */}
        <div className="lg:col-span-5 flex flex-col">
          <motion.div
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="bg-surface-container-low border border-outline-variant/30 rounded-3xl p-6 shadow-sm flex flex-col h-[500px]"
          >
            <div className="flex items-center gap-2 mb-4">
              <MessageSquare size={18} className="text-on-surface-variant" />
              <h2 className="text-base font-semibold">Live Transcript</h2>
            </div>
            
            {/* Transcript Scroll Area */}
            <div className="flex-1 overflow-y-auto custom-scrollbar space-y-3 pr-1">
              {transcript.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full text-center opacity-45 px-6">
                  <Mic size={40} className="mb-3" />
                  <p className="text-xs">No active conversation transcript yet. Start speaking to stream transcript.</p>
                </div>
              ) : (
                transcript.map((item) => (
                  <div
                    key={item.id}
                    className={`flex flex-col max-w-[85%] rounded-[18px] px-4 py-2.5 text-sm ${
                      item.type === 'ai'
                        ? "bg-primary/8 text-on-surface border border-primary/10 mr-auto rounded-tl-sm"
                        : "bg-surface-container-highest text-on-surface ml-auto rounded-tr-sm"
                    }`}
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-[10px] font-bold uppercase tracking-wider text-on-surface-variant">
                        {item.type === 'ai' ? 'AI Agent' : 'You'}
                      </span>
                      <span className="text-[9px] text-on-surface-variant/60">
                        {item.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                      </span>
                    </div>
                    <p className="leading-relaxed break-words">{item.text}</p>
                  </div>
                ))
              )}
              <div ref={transcriptEndRef} />
            </div>
          </motion.div>
        </div>
      </main>
    </div>
  );
}