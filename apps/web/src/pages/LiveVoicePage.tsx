import { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { useConfig, detectLanguage } from "@context";

interface TranscriptItem {
  id: number;
  type: 'user' | 'ai';
  text: string;
  timestamp: Date;
  lang: 'bn' | 'en';
}

const FILLERS_EN = ["Hmm..., ", "Let me think... ", "Okay, here's what I found: ", "So, ", "Well, ", "Let me check that for you... ", "Sure thing! ", "That's a good question! "];
const FILLERS_BN = ["হুম, ", "চিন্তা করি... ", "ঠিক আছে, ", "তাহলে, ", "আচ্ছা, ", "একটু দেখি... ", "অবশ্যই! ", "চমৎকার প্রশ্ন! "];

const selectBestVoice = (lang: string): SpeechSynthesisVoice | null => {
  if (!window.speechSynthesis) return null;
  const voices = window.speechSynthesis.getVoices();
  const langPrefix = lang.split('-')[0];
  return voices.find(v => v.lang.startsWith(langPrefix) && (v.localService || v.name.includes('Premium') || v.name.includes('Neural'))) || voices.find(v => v.lang.startsWith(langPrefix)) || null;
};

const addFiller = (text: string, lang: string): string => {
  if (!text.trim()) return text;
  const fillers = lang === 'bn' ? FILLERS_BN : FILLERS_EN;
  const isQuestion = text.trim().endsWith('?');
  const isGreeting = /^(hi|hello|hey|হ্যালো|হাই)/i.test(text.trim());
  if (!isQuestion && !isGreeting && Math.random() < 0.35) {
    return fillers[Math.floor(Math.random() * fillers.length)] + text;
  }
  return text;
};

const preprocessText = (text: string): string => {
  return text.replace(/\s+/g, ' ').replace(/([.!?]){2,}/g, '$1').replace(/,+/g, ',');
};

const getApiUrl = () => import.meta.env.VITE_API_URL || 'http://localhost:8000';
const getWsUrl = () => {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  return import.meta.env.VITE_WS_URL || `${protocol}//${window.location.hostname}:8000`;
};

const JarvisOrb = ({ isSpeaking, isListening, isMuted }: { isSpeaking: boolean; isListening: boolean; isMuted: boolean }) => {
  const colors = {
    idle: { inner: 'from-slate-800/40 to-slate-900/60', border: 'border-slate-500/40', glow: 'shadow-slate-500/20' },
    listening: { inner: 'from-blue-500/30 to-indigo-500/30', border: 'border-blue-400/60', glow: 'shadow-blue-400/30' },
    speaking: { inner: 'from-emerald-500/30 to-cyan-500/30', border: 'border-emerald-400/60', glow: 'shadow-emerald-400/30' },
    muted: { inner: 'from-red-500/20 to-red-900/30', border: 'border-red-400/50', glow: 'shadow-red-400/20' },
  };
  
  const status = isMuted ? 'muted' : isSpeaking ? 'speaking' : isListening ? 'listening' : 'idle';
  const c = colors[status];
  
  return (
    <div className="relative w-72 h-72 flex items-center justify-center">
      {[2, 1.4, 1.15].map((scale, i) => (
        <motion.div
          key={scale}
          animate={{
            scale: isSpeaking ? [1, 1.1, 1] : isListening ? [1, 1.04, 1] : 1,
            opacity: isSpeaking ? [0.15 - i * 0.04, 0.03, 0.15 - i * 0.04] : isListening ? [0.1 - i * 0.03, 0.02, 0.1 - i * 0.03] : 0.08 - i * 0.02,
          }}
          transition={{ duration: 2 + i * 0.5, repeat: Infinity, ease: "easeInOut", delay: i * 0.3 }}
          className={`absolute rounded-full bg-gradient-to-br ${c.inner} border ${c.border}`}
          style={{ width: '100%', height: '100%' }}
        />
      ))}

      <motion.div
        animate={{ rotate: isSpeaking || isListening ? 360 : 0 }}
        transition={{ duration: 25, repeat: Infinity, ease: "linear" }}
        className="absolute w-80 h-80"
      >
        {[0, 120, 240].map((deg, i) => (
          <motion.div
            key={deg}
            animate={{ opacity: isSpeaking ? [0.8, 0.3, 0.8] : isListening ? [0.6, 0.2, 0.6] : [0.4, 0.2, 0.4] }}
            transition={{ duration: 2, repeat: Infinity, delay: i * 0.5 }}
            className={`absolute w-2 h-2 rounded-full ${isSpeaking ? 'bg-emerald-400' : isListening ? 'bg-blue-400' : 'bg-slate-400'}`}
            style={{ 
              top: '50%', 
              left: '50%', 
              transform: `rotate(${deg}deg) translateY(-140px)`,
            }}
          />
        ))}
      </motion.div>

      <motion.div
        animate={{ scale: isSpeaking || isListening ? [1, 1.03, 1] : 1 }}
        transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
        className={`relative w-48 h-48 rounded-full border-[3px] shadow-2xl flex flex-col items-center justify-center bg-gradient-to-br ${c.inner} ${c.border} ${c.glow}`}
      >
        <div className="flex gap-1 h-6 items-end">
          {[0.0, 0.15, 0.3, 0.45, 0.6, 0.75, 0.9, 1.05].map((delay, i) => (
            <motion.div
              key={i}
              animate={isSpeaking || isListening ? {
                height: [12, 32, 12],
              } : { height: 12 }}
              transition={{
                duration: 0.8,
                repeat: Infinity,
                delay: delay,
                ease: "easeInOut"
              }}
              className={`w-1.5 rounded-full ${isSpeaking ? 'bg-emerald-400' : isListening ? 'bg-blue-400' : 'bg-slate-500/50'}`}
            />
          ))}
        </div>
        
        <div className="mt-3 text-center">
          <span className="text-xs font-medium tracking-wider uppercase">
            {isMuted ? 'Muted' : isSpeaking ? 'Speaking' : isListening ? 'Listening' : 'Ready'}
          </span>
        </div>
      </motion.div>
    </div>
  );
};

export function LiveVoicePage() {
  const navigate = useNavigate();
  const { language, setLanguage, effectiveLanguage, voiceModel, setVoiceModel, voiceMode } = useConfig();
  
  const [isMuted, setIsMuted] = useState(false);
  const [isCallActive, setIsCallActive] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [transcript, setTranscript] = useState<TranscriptItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [showSettings, setShowSettings] = useState(false);
  const [isSpeechSupported, setIsSpeechSupported] = useState(true);
  const [currentLang, setCurrentLang] = useState<'bn' | 'en'>(effectiveLanguage);
  const [micPermission, setMicPermission] = useState<'pending' | 'granted' | 'denied'>('pending');
  const [isRequestingMic, setIsRequestingMic] = useState(false);

  const recognitionRef = useRef<any>(null);
  const transcriptIdRef = useRef(0);
  const isSpeakingRef = useRef(false);
  const wsRef = useRef<WebSocket | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const audioQueueRef = useRef<AudioBuffer[]>([]);
  const isPlayingRef = useRef(false);
  const transcriptEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setIsSpeechSupported(false);
      return;
    }
    
    navigator.permissions?.query({ name: 'microphone' }).then(result => {
      setMicPermission(result.state === 'granted' ? 'granted' : 'pending');
      result.onchange = () => {
        setMicPermission(result.state === 'granted' ? 'granted' : 'denied');
      };
    }).catch(() => {});
    
    const loadVoices = () => { if (window.speechSynthesis) window.speechSynthesis.getVoices(); };
    loadVoices();
    if (window.speechSynthesis) window.speechSynthesis.onvoiceschanged = loadVoices;

    return () => { cleanupCallResources(); };
  }, []);

  useEffect(() => {
    transcriptEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [transcript]);

  const requestMicPermission = async () => {
    setIsRequestingMic(true);
    try {
      await navigator.mediaDevices.getUserMedia({ audio: true });
      setMicPermission('granted');
      return true;
    } catch {
      setMicPermission('denied');
      return false;
    } finally {
      setIsRequestingMic(false);
    }
  };

  const cleanupCallResources = () => {
    if (recognitionRef.current) { recognitionRef.current.stop(); recognitionRef.current = null; }
    if (window.speechSynthesis) window.speechSynthesis.cancel();
    if (wsRef.current) disconnectWebSocket();
    if (audioContextRef.current) { audioContextRef.current.close(); audioContextRef.current = null; }
  };

  const initAudioContext = () => {
    if (!audioContextRef.current) audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)();
    if (audioContextRef.current.state === 'suspended') audioContextRef.current.resume();
    return audioContextRef.current;
  };

  const playAudioChunk = async (base64Audio: string) => {
    try {
      const audioContext = initAudioContext();
      const binaryString = atob(base64Audio);
      const bytes = new Uint8Array(binaryString.length);
      for (let i = 0; i < binaryString.length; i++) bytes[i] = binaryString.charCodeAt(i);
      const audioBuffer = await audioContext.decodeAudioData(bytes.buffer);
      audioQueueRef.current.push(audioBuffer);
      if (!isPlayingRef.current) playNextAudio();
    } catch (err) { console.error('Error playing audio chunk:', err); }
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
    if (!buffer) { playNextAudio(); return; }
    const source = audioContext.createBufferSource();
    source.buffer = buffer;
    source.connect(audioContext.destination);
    source.onended = () => {
      if (audioQueueRef.current.length > 0) playNextAudio();
      else { isPlayingRef.current = false; isSpeakingRef.current = false; setIsSpeaking(false); }
    };
    source.start(0);
  };

  const connectWebSocket = (userId: number = 1) => {
    return new Promise<void>((resolve, reject) => {
      const ws = new WebSocket(`${getWsUrl()}/voice/ws/${userId}`);
      wsRef.current = ws;
      ws.onopen = () => { resolve(); };
      ws.onmessage = async (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'audio_chunk') {
          if (data.audio) { isSpeakingRef.current = true; setIsSpeaking(true); await playAudioChunk(data.audio); }
          if (data.text) appendOrUpdateTranscript(data.text, 'ai', currentLang);
        } else if (data.type === 'response_text' && data.text) {
          appendOrUpdateTranscript(data.text, 'ai', currentLang);
        } else if (data.type === 'complete') { isSpeakingRef.current = false; setIsSpeaking(false); }
        else if (data.type === 'interrupted') { audioQueueRef.current = []; isPlayingRef.current = false; isSpeakingRef.current = false; setIsSpeaking(false); }
        else if (data.type === 'error') setError(data.message);
      };
      ws.onerror = (err) => { console.error('WebSocket error:', err); reject(err); };
      ws.onclose = () => { wsRef.current = null; };
    });
  };

  const appendOrUpdateTranscript = (text: string, type: 'user' | 'ai', lang: 'bn' | 'en') => {
    if (!text.trim()) return;
    const detectedLang = type === 'user' ? detectLanguage(text) : lang;
    if (type === 'user' && detectedLang !== currentLang) setCurrentLang(detectedLang);
    setTranscript(prev => {
      const last = prev[prev.length - 1];
      if (last && last.type === type && type === 'ai') return [...prev.slice(0, -1), { ...last, text, timestamp: new Date() }];
      return [...prev, { id: transcriptIdRef.current++, type, text, timestamp: new Date(), lang: detectedLang }];
    });
  };

  const sendInterrupt = () => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) wsRef.current.send(JSON.stringify({ type: 'interrupt' }));
    audioQueueRef.current = [];
    isPlayingRef.current = false;
    if (window.speechSynthesis) window.speechSynthesis.cancel();
    isSpeakingRef.current = false;
    setIsSpeaking(false);
  };

  const sendTextMessage = async (text: string) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) wsRef.current.send(JSON.stringify({ type: 'text', data: text, language: currentLang }));
  };

  const disconnectWebSocket = () => {
    if (wsRef.current) {
      try { wsRef.current.send(JSON.stringify({ type: 'end' })); } catch {}
      wsRef.current.close();
      wsRef.current = null;
    }
    audioQueueRef.current = [];
    isPlayingRef.current = false;
  };

  const initSpeechRecognition = async () => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) { setError('Speech recognition not supported. Use Chrome or Edge.'); return false; }
    
    const hasPermission = micPermission === 'granted' ? true : await requestMicPermission();
    if (!hasPermission) { setError('Microphone access denied. Please allow microphone access.'); return false; }

    recognitionRef.current = new SpeechRecognition();
    recognitionRef.current.continuous = true;
    recognitionRef.current.interimResults = true;
    recognitionRef.current.lang = currentLang === 'bn' ? 'bn-BD' : 'en-US';

    recognitionRef.current.onstart = () => { setIsListening(true); setError(null); };
    recognitionRef.current.onresult = async (event: any) => {
      sendInterrupt();
      const result = event.results[event.results.length - 1];
      const transcriptText = result[0].transcript.trim();
      if (result.isFinal && transcriptText) await processUserSpeech(transcriptText);
    };
    recognitionRef.current.onerror = (event: any) => {
      console.error('Speech recognition error:', event.error);
      if (event.error === 'not-allowed') setError('Microphone access denied.');
      else if (event.error !== 'aborted' && event.error !== 'no-speech') setError(`Speech recognition error: ${event.error}`);
    };
    recognitionRef.current.onend = () => {
      if (isCallActive && !isMuted && recognitionRef.current) {
        try { recognitionRef.current.start(); } catch (e) { console.log('Recognition restart failed'); }
      }
    };
    return true;
  };

  const processUserSpeech = async (text: string) => {
    if (!text.trim()) return;
    const detectedLang = detectLanguage(text);
    if (detectedLang !== currentLang) {
      setCurrentLang(detectedLang);
      if (recognitionRef.current) recognitionRef.current.lang = detectedLang === 'bn' ? 'bn-BD' : 'en-US';
    }
    appendOrUpdateTranscript(text, 'user', detectedLang);

    try {
      if (voiceMode === 'streaming' && wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        isSpeakingRef.current = true; setIsSpeaking(true);
        await sendTextMessage(text);
      } else {
        setIsSpeaking(true); isSpeakingRef.current = true;
        const response = await fetch(`${getApiUrl()}/api/agents/gemini/chat/simple`, {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: text })
        });
        const data = await response.json();
        let aiResponse = data.response || data.error || 'Sorry, I could not process that request.';
        aiResponse = preprocessText(aiResponse);
        aiResponse = addFiller(aiResponse, currentLang);
        appendOrUpdateTranscript(aiResponse, 'ai', currentLang);
        speakText(aiResponse);
      }
    } catch (err) {
      console.error('Failed to process speech input:', err);
      appendOrUpdateTranscript(preprocessText('Sorry, I encountered an error. Please try again.'), 'ai', currentLang);
    }
  };

  const speakText = (text: string) => {
    if (!window.speechSynthesis) return;
    window.speechSynthesis.cancel();
    const sentences = text.match(/[^.!?।]+[.!?।]+/g) || [text];
    const voice = selectBestVoice(currentLang === 'bn' ? 'bn-BD' : 'en-US');
    const baseRate = text.length > 200 ? 1.1 : 1.05;
    let completedCount = 0;
    const totalSentences = sentences.length;

    sentences.forEach((sentence, index) => {
      const cleanSentence = sentence.trim();
      if (!cleanSentence) return;
      setTimeout(() => {
        if (!isSpeakingRef.current && index > 0) return;
        const utterance = new SpeechSynthesisUtterance(cleanSentence);
        utterance.lang = currentLang === 'bn' ? 'bn-BD' : 'en-US';
        utterance.rate = baseRate;
        utterance.pitch = 1.02;
        if (voice) utterance.voice = voice;
        utterance.onstart = () => { isSpeakingRef.current = true; setIsSpeaking(true); };
        utterance.onend = () => { completedCount++; if (completedCount >= totalSentences) { isSpeakingRef.current = false; setIsSpeaking(false); } };
        utterance.onerror = () => { completedCount++; if (completedCount >= totalSentences) { isSpeakingRef.current = false; setIsSpeaking(false); } };
        window.speechSynthesis.speak(utterance);
      }, index * 100);
    });
  };

  const startCall = async () => {
    try {
      setError(null);
      setTranscript([]);
      setCurrentLang(effectiveLanguage);
      const initialized = await initSpeechRecognition();
      if (!initialized) return;

      setIsCallActive(true);
      if (voiceMode === 'streaming') {
        try { await connectWebSocket(1); } catch (wsErr) { console.warn('WebSocket failed, using HTTP fallback:', wsErr); }
      }

      setTimeout(() => {
        if (recognitionRef.current) {
          try { recognitionRef.current.start(); } catch (e) { console.error('Failed to start recognition:', e); }
        }
      }, 500);

      const welcomeMessage = currentLang === 'bn' ? "হ্যালো! আমি আপনার AI সহকারী। আজ আপনাকে কীভাবে সাহায্য করতে পারি?" : "Hello! I'm your AI assistant. How can I help you today?";
      
      setTimeout(() => {
        if (voiceMode === 'streaming' && wsRef.current && wsRef.current.readyState === WebSocket.OPEN) sendTextMessage(welcomeMessage);
        else speakText(welcomeMessage);
        setTranscript([{ id: 0, type: 'ai', text: welcomeMessage, timestamp: new Date(), lang: currentLang }]);
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
      try { recognitionRef.current.start(); setIsMuted(false); } catch (e) { console.error('Failed to resume recognition'); }
    } else if (recognitionRef.current) {
      recognitionRef.current.stop();
      setIsMuted(true);
      setIsListening(false);
    }
  };

  const quickPrompts = currentLang === 'bn' ? ["আমার সিজিপিএ কত?", "কী কী বই পাওয়া যাবে?", "শাটল বাস এর শিডিউল?", "রেজুমে তৈরিতে সাহায্য করুন"] : ["What's my CGPA?", "Show available books", "Shuttle schedule?", "Help with resume"];

  return (
    <div className="min-h-screen bg-white dark:bg-[#1a1a1a] text-gray-900 dark:text-gray-100 flex flex-col transition-colors duration-300">
      <header className="w-full px-8 py-4 flex items-center justify-between border-b border-gray-200 dark:border-gray-800">
        <div className="flex items-center gap-3">
          <button onClick={() => navigate("/intelligence")} className="text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100 transition-colors cursor-pointer text-sm font-medium">
            ← Back
          </button>
          <div className="h-4 w-px bg-gray-200 dark:bg-gray-700" />
          <span className="text-base font-medium">Daffodil Intelligence</span>
        </div>
        
        <div className="flex items-center gap-4">
          <span className="text-xs text-gray-500 dark:text-gray-400">{currentLang === 'bn' ? 'বাংলা' : 'English'}</span>
          <div className={`px-3 py-1 rounded-full text-xs font-medium ${isCallActive ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400' : 'bg-gray-100 dark:bg-gray-800 text-gray-500'}`}>
            {isCallActive ? '● Live' : '○ Ready'}
          </div>
        </div>
      </header>

      <main className="flex-1 flex flex-col items-center justify-center px-6 py-12">
        <JarvisOrb isSpeaking={isSpeaking} isListening={isListening} isMuted={isMuted} />
        
        <div className="mt-10 text-center max-w-lg">
          <h2 className="text-2xl font-normal tracking-tight mb-2">
            {isCallActive ? (isMuted ? 'Muted' : isSpeaking ? 'Speaking...' : isListening ? 'Listening...' : 'Connected') : 'Voice Assistant'}
          </h2>
          <p className="text-sm text-gray-500 dark:text-gray-400 mb-8">
            {isCallActive ? 'Tap to mute or end the conversation' : 'Your intelligent assistant with auto language detection'}
          </p>

          {error && (
            <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-2xl text-sm text-red-600 dark:text-red-400">
              {error}
            </div>
          )}

          {!isCallActive && (
            <div className="flex flex-col items-center gap-4">
              <button
                onClick={() => setShowSettings(!showSettings)}
                className="text-sm text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100 transition-colors"
              >
                {showSettings ? 'Hide Settings' : 'Settings'}
              </button>

              <AnimatePresence>
                {showSettings && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: "auto" }}
                    exit={{ opacity: 0, height: 0 }}
                    className="w-full max-w-sm overflow-hidden"
                  >
                    <div className="pt-4 space-y-3">
                      <div>
                        <label className="text-xs text-gray-500 block mb-1.5">Language</label>
                        <select
                          value={language}
                          onChange={(e) => setLanguage(e.target.value as any)}
                          className="w-full px-4 py-2.5 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 cursor-pointer"
                        >
                          <option value="auto">Auto Detect</option>
                          <option value="en">English</option>
                          <option value="bn">বাংলা (Bangla)</option>
                        </select>
                      </div>
                      <div>
                        <label className="text-xs text-gray-500 block mb-1.5">Voice Model</label>
                        <select
                          value={voiceModel}
                          onChange={(e) => setVoiceModel(e.target.value)}
                          className="w-full px-4 py-2.5 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 cursor-pointer"
                        >
                          <option value="Aoede">Aoede</option>
                          <option value="Puck">Puck</option>
                          <option value="Charon">Charon</option>
                          <option value="Ernie">Ernie</option>
                          <option value="Fenrir">Fenrir</option>
                        </select>
                      </div>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>

              <button
                onClick={startCall}
                disabled={!isSpeechSupported || isRequestingMic}
                className="mt-6 px-10 py-4 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 dark:disabled:bg-gray-700 text-white disabled:text-gray-500 rounded-full font-medium text-base transition-all shadow-lg"
              >
                {isRequestingMic ? 'Requesting mic...' : 'Start Conversation'}
              </button>

              {!isSpeechSupported && (
                <p className="text-xs text-red-500 mt-2">Web Speech API not supported in this browser</p>
              )}
            </div>
          )}

          {isCallActive && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex flex-col items-center gap-4">
              <div className="flex items-center justify-center gap-4">
                <button
                  onClick={toggleMute}
                  className={`px-6 py-3 rounded-full font-medium text-sm transition-all ${isMuted ? 'bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400' : 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300'}`}
                >
                  {isMuted ? 'Unmute' : 'Mute'}
                </button>
                <button
                  onClick={sendInterrupt}
                  className="px-6 py-3 rounded-full font-medium text-sm bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 transition-all"
                >
                  {isSpeaking ? 'Stop' : 'Pause'}
                </button>
                <button
                  onClick={endCall}
                  className="px-6 py-3 rounded-full font-medium text-sm bg-gray-900 dark:bg-gray-100 text-white dark:text-gray-900 transition-all"
                >
                  End
                </button>
              </div>

              <div className="flex flex-wrap items-center justify-center gap-2 mt-2 max-w-lg px-4">
                {quickPrompts.map((promptText, i) => (
                  <button
                    key={i}
                    onClick={() => processUserSpeech(promptText)}
                    className="px-4 py-1.5 text-xs font-medium bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 rounded-full hover:bg-gray-200 dark:hover:bg-gray-700 transition-all cursor-pointer"
                  >
                    {promptText}
                  </button>
                ))}
              </div>
            </motion.div>
          )}
        </div>

        {transcript.length > 0 && (
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="w-full max-w-xl mt-12">
            <div className="bg-gray-50 dark:bg-gray-900/50 rounded-2xl p-4 max-h-72 overflow-y-auto">
              <div className="space-y-3">
                {transcript.map((item) => (
                  <div key={item.id} className={`flex ${item.type === 'user' ? 'justify-end' : 'justify-start'}`}>
                    <div className={`max-w-[80%] rounded-2xl px-4 py-3 ${item.type === 'ai' ? 'bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100' : 'bg-blue-600 text-white'}`}>
                      <p className="text-sm leading-relaxed">{item.text}</p>
                      <span className="text-[10px] opacity-60 mt-1 block">{item.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                    </div>
                  </div>
                ))}
                <div ref={transcriptEndRef} />
              </div>
            </div>
          </motion.div>
        )}
      </main>
    </div>
  );
}