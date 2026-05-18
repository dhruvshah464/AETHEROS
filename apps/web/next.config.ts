import type { NextConfig } from 'next';
import path from 'path';

const nextConfig: NextConfig = {
  transpilePackages: ['@aetheros/types', '@aetheros/events'],
  reactStrictMode: true,
  outputFileTracingRoot: path.join(__dirname, '../..'),
};

export default nextConfig;
