import { useCallback, useEffect, useRef, useState } from "react";

const MAX_RECORDING_MS = 60 * 60 * 1000; // 1 hour

export interface VoiceRecording {
  blob: Blob;
  mimeType: string;
  durationMs: number;
}

export interface AudioInputDevice {
  deviceId: string;
  label: string;
}

function pickMimeType(): string {
  const candidates = [
    "audio/webm;codecs=opus",
    "audio/webm",
    "audio/ogg;codecs=opus",
    "audio/mp4",
  ];
  if (typeof MediaRecorder === "undefined") return "audio/webm";
  return candidates.find((t) => MediaRecorder.isTypeSupported(t)) ?? "audio/webm";
}

export function useVoiceRecorder() {
  const [isRecording, setIsRecording] = useState(false);
  const [recording, setRecording] = useState<VoiceRecording | null>(null);
  const [levels, setLevels] = useState<number[]>([0.2, 0.35, 0.5, 0.35, 0.2]);
  const [devices, setDevices] = useState<AudioInputDevice[]>([]);
  const [selectedDeviceId, setSelectedDeviceId] = useState<string>("");

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const startedAtRef = useRef<number>(0);
  const maxTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const rafRef = useRef<number | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);

  const cleanupStream = useCallback(() => {
    if (rafRef.current != null) {
      cancelAnimationFrame(rafRef.current);
      rafRef.current = null;
    }
    if (maxTimerRef.current) {
      clearTimeout(maxTimerRef.current);
      maxTimerRef.current = null;
    }
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
    mediaRecorderRef.current = null;
    analyserRef.current = null;
    if (audioContextRef.current) {
      void audioContextRef.current.close();
      audioContextRef.current = null;
    }
  }, []);

  const refreshDevices = useCallback(async () => {
    if (!navigator.mediaDevices?.enumerateDevices) return;
    const list = await navigator.mediaDevices.enumerateDevices();
    const inputs = list
      .filter((d) => d.kind === "audioinput")
      .map((d, i) => ({
        deviceId: d.deviceId,
        label: d.label || `Microphone ${i + 1}`,
      }));
    setDevices(inputs);
    if (!selectedDeviceId && inputs[0]) {
      setSelectedDeviceId(inputs[0].deviceId);
    }
  }, [selectedDeviceId]);

  const stopRecording = useCallback(() => {
    const recorder = mediaRecorderRef.current;
    if (!recorder || recorder.state === "inactive") return;
    recorder.stop();
  }, []);

  const discardRecording = useCallback(() => {
    setRecording(null);
  }, []);

  const startLevelMeter = useCallback((analyser: AnalyserNode) => {
    const data = new Uint8Array(analyser.frequencyBinCount);
    const tick = () => {
      analyser.getByteFrequencyData(data);
      const slice = 5;
      const step = Math.max(1, Math.floor(data.length / slice));
      const next = Array.from({ length: slice }, (_, i) => {
        const start = i * step;
        let sum = 0;
        for (let j = 0; j < step; j++) sum += data[start + j] ?? 0;
        const avg = sum / step / 255;
        return Math.max(0.12, Math.min(1, avg * 1.8));
      });
      setLevels(next);
      rafRef.current = requestAnimationFrame(tick);
    };
    rafRef.current = requestAnimationFrame(tick);
  }, []);

  const startRecording = useCallback(async () => {
    if (isRecording) return;
    if (!navigator.mediaDevices?.getUserMedia) {
      throw new Error("Microphone access is not supported in this browser");
    }

    setRecording(null);
    chunksRef.current = [];

    const constraints: MediaStreamConstraints = {
      audio: selectedDeviceId ? { deviceId: { exact: selectedDeviceId } } : true,
    };
    const stream = await navigator.mediaDevices.getUserMedia(constraints);
    streamRef.current = stream;

    const audioContext = new AudioContext();
    audioContextRef.current = audioContext;
    const source = audioContext.createMediaStreamSource(stream);
    const analyser = audioContext.createAnalyser();
    analyser.fftSize = 256;
    source.connect(analyser);
    analyserRef.current = analyser;
    startLevelMeter(analyser);

    const mimeType = pickMimeType();
    const recorder = new MediaRecorder(stream, { mimeType });
    mediaRecorderRef.current = recorder;
    startedAtRef.current = Date.now();

    recorder.ondataavailable = (event) => {
      if (event.data.size > 0) chunksRef.current.push(event.data);
    };

    recorder.onstop = () => {
      const durationMs = Date.now() - startedAtRef.current;
      const blob = new Blob(chunksRef.current, { type: mimeType });
      cleanupStream();
      setIsRecording(false);
      if (blob.size > 0) {
        setRecording({ blob, mimeType, durationMs });
      }
    };

    recorder.start(250);
    setIsRecording(true);
    void refreshDevices();

    maxTimerRef.current = setTimeout(() => {
      stopRecording();
    }, MAX_RECORDING_MS);
  }, [
    cleanupStream,
    isRecording,
    refreshDevices,
    selectedDeviceId,
    startLevelMeter,
    stopRecording,
  ]);

  useEffect(() => {
    return () => cleanupStream();
  }, [cleanupStream]);

  return {
    isRecording,
    recording,
    levels,
    devices,
    selectedDeviceId,
    setSelectedDeviceId,
    refreshDevices,
    startRecording,
    stopRecording,
    discardRecording,
  };
}
