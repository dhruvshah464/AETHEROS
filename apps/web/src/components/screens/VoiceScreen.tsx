'use client';

import { useState, useRef, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Mic, MicOff } from 'lucide-react';
import { HUDPanel } from '@/components/hud/HUDPanel';
import { useAetherStore } from '@/store/aether-store';
import { API_URL } from '@/lib/utils';

export function VoiceScreen() {
  const {
    voiceActive,
    transcript,
    voiceResponse,
    voiceAudio,
    voiceSpeaking,
    setVoiceActive,
    setTranscript,
    setVoiceResponse,
    setVoiceAudio,
  } = useAetherStore();
  const [listening, setListening] = useState(false);
  const [processing, setProcessing] = useState(false);
  const mediaRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    if (voiceAudio && audioRef.current) {
      audioRef.current.src = `data:audio/mp3;base64,${voiceAudio}`;
      audioRef.current.play().catch(() => {});
    }
  }, [voiceAudio]);

  const startListening = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
      chunksRef.current = [];
      recorder.ondataavailable = (e) => chunksRef.current.push(e.data);
      recorder.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
        const reader = new FileReader();
        reader.onloadend = async () => {
          const b64 = (reader.result as string).split(',')[1];
          setProcessing(true);
          const res = await fetch(`${API_URL}/voice/converse`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ audio: b64, format: 'webm' }),
          });
          const data = await res.json();
          setTranscript(data.transcript || '');
          setVoiceResponse(data.response || '');
          if (data.audio) setVoiceAudio(data.audio);
          setProcessing(false);
        };
        reader.readAsDataURL(blob);
      };
      mediaRef.current = recorder;
      recorder.start();
      setListening(true);
      setVoiceActive(true);
    } catch {
      setTranscript('Microphone access required for Jarvis mode');
    }
  };

  const stopListening = () => {
    mediaRef.current?.stop();
    setListening(false);
    setVoiceActive(false);
  };

  return (
    <div className="flex flex-col items-center justify-center h-full gap-8">
      <audio ref={audioRef} className="hidden" />
      <HUDPanel title="Voice Interface — AETHER Jarvis" className="max-w-2xl w-full" delay={0.1}>
        <motion.div className="p-8 flex flex-col items-center gap-8">
          {/* Holographic waveform rings */}
          {listening && (
            <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
              {[1, 2, 3].map((ring) => (
                <motion.div
                  key={ring}
                  animate={{ scale: [1, 1.5 + ring * 0.2], opacity: [0.4, 0] }}
                  transition={{ repeat: Infinity, duration: 2, delay: ring * 0.3 }}
                  className="absolute w-40 h-40 rounded-full border border-aether-cyan/30"
                />
              ))}
            </div>
          )}

          <motion.button
            onClick={listening ? stopListening : startListening}
            disabled={processing}
            animate={
              listening || voiceSpeaking
                ? { boxShadow: ['0 0 30px #00f0ff44', '0 0 60px #00f0ff88', '0 0 30px #00f0ff44'] }
                : {}
            }
            transition={{ repeat: Infinity, duration: 2 }}
            className={`relative w-32 h-32 rounded-full border-2 flex items-center justify-center transition-all ${
              listening ? 'border-aether-cyan bg-aether-cyan/10' : 'border-aether-cyan/30'
            }`}
          >
            {listening ? <Mic className="w-12 h-12 text-aether-cyan" /> : <MicOff className="w-12 h-12 text-aether-cyan/40" />}
          </motion.button>

          <span className="hud-label">
            {processing ? 'PROCESSING...' : listening ? 'LISTENING — Tap to send' : 'Push to talk — Hey Aether'}
          </span>

          {(listening || voiceSpeaking) && (
            <div className="flex gap-1 h-16 items-end w-72">
              {Array.from({ length: 32 }).map((_, i) => (
                <motion.div
                  key={i}
                  animate={{ height: ['15%', `${20 + Math.random() * 80}%`, '15%'] }}
                  transition={{ repeat: Infinity, duration: 0.25 + Math.random() * 0.4, delay: i * 0.03 }}
                  className="flex-1 bg-aether-cyan/60 rounded-sm"
                  style={{ boxShadow: '0 0 6px #00f0ff' }}
                />
              ))}
            </div>
          )}

          {transcript && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="w-full p-4 border border-aether-border/30"
            >
              <span className="hud-label">You</span>
              <p className="font-mono text-sm text-aether-cyan/80 mt-1">{transcript}</p>
            </motion.div>
          )}

          {voiceResponse && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="w-full p-4 border border-aether-purple/30"
            >
              <span className="hud-label text-aether-purple">AETHER</span>
              <p className="font-mono text-sm text-aether-cyan/90 mt-1">{voiceResponse}</p>
            </motion.div>
          )}
        </motion.div>
      </HUDPanel>
    </div>
  );
}
