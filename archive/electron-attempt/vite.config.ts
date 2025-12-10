import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { resolve } from 'path';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
      '@renderer': resolve(__dirname, 'src/renderer'),
      '@main': resolve(__dirname, 'src/main'),
      '@shared': resolve(__dirname, 'src/shared'),
      '@components': resolve(__dirname, 'src/renderer/components'),
    },
  },
  base: './',
  build: {
    outDir: 'dist/renderer',
  },
  server: {
    port: 5173,
    strictPort: true,
  },
});
