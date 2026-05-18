import type { Config } from 'tailwindcss';

const config: Config = {
  content: ['./src/**/*.{js,ts,jsx,tsx,mdx}'],
  theme: {
    extend: {
      colors: {
        aether: {
          cyan: '#00f0ff',
          blue: '#0088ff',
          purple: '#7b61ff',
          green: '#00ff88',
          gold: '#ffd700',
          red: '#ff3366',
          dark: '#0a0e17',
          panel: 'rgba(0, 240, 255, 0.03)',
          border: 'rgba(0, 240, 255, 0.15)',
        },
      },
      fontFamily: {
        hud: ['var(--font-orbitron)', 'monospace'],
        mono: ['var(--font-jetbrains)', 'monospace'],
      },
      animation: {
        'pulse-glow': 'pulse-glow 2s ease-in-out infinite',
        'scan-line': 'scan-line 4s linear infinite',
        'radar-sweep': 'radar-sweep 4s linear infinite',
        'flicker': 'flicker 0.15s infinite',
      },
      keyframes: {
        'pulse-glow': {
          '0%, 100%': { opacity: '0.4' },
          '50%': { opacity: '1' },
        },
        'scan-line': {
          '0%': { transform: 'translateY(-100%)' },
          '100%': { transform: 'translateY(100vh)' },
        },
        'radar-sweep': {
          '0%': { transform: 'rotate(0deg)' },
          '100%': { transform: 'rotate(360deg)' },
        },
        flicker: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.97' },
        },
      },
      boxShadow: {
        hud: '0 0 20px rgba(0, 240, 255, 0.15), inset 0 0 20px rgba(0, 240, 255, 0.05)',
        'hud-lg': '0 0 40px rgba(0, 240, 255, 0.2), inset 0 0 30px rgba(0, 240, 255, 0.08)',
      },
    },
  },
  plugins: [],
};

export default config;
