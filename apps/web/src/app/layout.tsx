import type { Metadata } from 'next';
import { Orbitron, JetBrains_Mono } from 'next/font/google';
import './globals.css';

const orbitron = Orbitron({
  subsets: ['latin'],
  variable: '--font-orbitron',
  weight: ['400', '500', '700', '900'],
});

const jetbrains = JetBrains_Mono({
  subsets: ['latin'],
  variable: '--font-jetbrains',
  weight: ['300', '400', '500', '700'],
});

export const metadata: Metadata = {
  title: 'AetherOS — AI Operating Interface',
  description:
    'Cinematic AI Operating System. Iron Man HUD meets production-grade autonomous agent infrastructure.',
  keywords: ['AI', 'HUD', 'operating system', 'agents', 'Jarvis', 'open source'],
  openGraph: {
    title: 'AetherOS',
    description: 'The AI Operating Interface from the future.',
    type: 'website',
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${orbitron.variable} ${jetbrains.variable}`}>
      <body className="font-mono antialiased">{children}</body>
    </html>
  );
}
