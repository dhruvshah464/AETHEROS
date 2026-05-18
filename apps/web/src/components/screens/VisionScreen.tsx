'use client';

import { useRef, useEffect, useState, useCallback } from 'react';
import { motion } from 'framer-motion';
import { Camera, CameraOff, Monitor } from 'lucide-react';
import { HUDPanel } from '@/components/hud/HUDPanel';
import { useAetherStore } from '@/store/aether-store';
import { API_URL } from '@/lib/utils';

export function VisionScreen() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [active, setActive] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { detections, setDetections, sceneAnalysis, setSceneAnalysis, screenCapture, setScreenCapture } =
    useAetherStore();
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: 640, height: 480, facingMode: 'user' },
      });
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
        setActive(true);
        setError(null);
      }
    } catch {
      setError('Camera access denied or unavailable');
    }
  };

  const stopCamera = () => {
    if (videoRef.current?.srcObject) {
      const tracks = (videoRef.current.srcObject as MediaStream).getTracks();
      tracks.forEach((t) => t.stop());
      videoRef.current.srcObject = null;
    }
    if (intervalRef.current) clearInterval(intervalRef.current);
    setActive(false);
    setDetections([]);
  };

  const captureAndDetect = useCallback(async () => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas || video.readyState < 2) return;

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    ctx.drawImage(video, 0, 0);
    const dataUrl = canvas.toDataURL('image/jpeg', 0.7);
    const frame = dataUrl.split(',')[1];

    try {
      const res = await fetch(`${API_URL}/vision/detect`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ frame }),
      });
      const data = await res.json();
      if (data.detections) setDetections(data.detections);
    } catch {
      // API offline — show scan aesthetic only
    }
  }, [setDetections]);

  useEffect(() => {
    if (active) {
      intervalRef.current = setInterval(captureAndDetect, 500);
    }
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [active, captureAndDetect]);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 h-full">
      <HUDPanel title="Visual Intelligence Feed" className="lg:col-span-2" delay={0.1}>
        <div className="relative p-4">
          <div className="relative aspect-video bg-black/60 border border-aether-border/30 overflow-hidden">
            <video ref={videoRef} className="w-full h-full object-cover" playsInline muted />
            <canvas ref={canvasRef} className="hidden" />

            {/* Scan overlay */}
            <div className="absolute inset-0 pointer-events-none">
              <div className="absolute top-4 left-4 w-8 h-8 border-t border-l border-aether-cyan/60" />
              <div className="absolute top-4 right-4 w-8 h-8 border-t border-r border-aether-cyan/60" />
              <div className="absolute bottom-4 left-4 w-8 h-8 border-b border-l border-aether-cyan/60" />
              <div className="absolute bottom-4 right-4 w-8 h-8 border-b border-r border-aether-cyan/60" />

              {active && (
                <motion.div
                  animate={{ top: ['0%', '100%', '0%'] }}
                  transition={{ repeat: Infinity, duration: 3, ease: 'linear' }}
                  className="absolute left-0 right-0 h-px bg-aether-cyan/60"
                  style={{ boxShadow: '0 0 10px #00f0ff' }}
                />
              )}

              {/* Detection boxes */}
              {detections.map((d, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="absolute border border-aether-green/80"
                  style={{
                    left: `${d.bbox[0] * 100}%`,
                    top: `${d.bbox[1] * 100}%`,
                    width: `${d.bbox[2] * 100}%`,
                    height: `${d.bbox[3] * 100}%`,
                  }}
                >
                  <span className="absolute -top-5 left-0 font-mono text-[10px] text-aether-green bg-black/80 px-1">
                    {d.label} {(d.confidence * 100).toFixed(0)}%
                  </span>
                </motion.div>
              ))}
            </div>

            {!active && (
              <div className="absolute inset-0 flex flex-col items-center justify-center gap-4">
                <CameraOff className="w-12 h-12 text-aether-cyan/20" />
                <p className="hud-label">{error || 'Camera offline'}</p>
              </div>
            )}
          </div>

          <div className="flex flex-wrap gap-2 mt-4">
            <button onClick={active ? stopCamera : startCamera} className="hud-btn flex items-center gap-2">
              <Camera size={14} />
              {active ? 'Deactivate' : 'Activate Vision'}
            </button>
            <button
              onClick={async () => {
                const res = await fetch(`${API_URL}/screen/analyze`, {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify({ question: 'What am I looking at on this screen?' }),
                });
                const data = await res.json();
                if (data.screenshot) setScreenCapture(data.screenshot);
                if (data.analysis) setSceneAnalysis(data.analysis);
              }}
              className="hud-btn flex items-center gap-2"
            >
              <Monitor size={14} /> Analyze Screen
            </button>
          </div>
        </div>
      </HUDPanel>

      <HUDPanel title="Intelligence Log" delay={0.2}>
        <div className="p-4 space-y-3 overflow-y-auto max-h-[400px]">
          {screenCapture && (
            <img
              src={`data:image/png;base64,${screenCapture}`}
              alt="Screen"
              className="w-full border border-aether-border/30 mb-2"
            />
          )}
          {sceneAnalysis && (
            <div className="p-2 border border-aether-purple/30 font-mono text-[10px] text-aether-cyan/80">
              <span className="hud-label text-aether-purple">Scene Analysis</span>
              <p className="mt-1">{sceneAnalysis}</p>
            </div>
          )}
          {detections.length === 0 ? (
            <p className="hud-label">No objects detected</p>
          ) : (
            detections.map((d, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: 10 }}
                animate={{ opacity: 1, x: 0 }}
                className="flex justify-between items-center p-2 border border-aether-border/20"
              >
                <span className="font-mono text-xs text-aether-green uppercase">{d.label}</span>
                <span className="hud-value">{(d.confidence * 100).toFixed(1)}%</span>
              </motion.div>
            ))
          )}
        </div>
      </HUDPanel>
    </div>
  );
}
