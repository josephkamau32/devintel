import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    // Enable source maps for production debugging
    sourcemap: false,
    // Reduce chunk size warnings threshold
    chunkSizeWarningLimit: 800,
    rollupOptions: {
      output: {
        // Smart code splitting for better caching
        manualChunks: {
          'vendor-react': ['react', 'react-dom'],
          'vendor-router': ['react-router-dom'],
          'vendor-state': ['zustand', '@tanstack/react-query'],
          'vendor-ui': ['lucide-react', 'react-hot-toast', 'clsx'],
          'vendor-http': ['axios'],
        },
      },
    },
    // Minification settings
    minify: 'esbuild',
    // Target modern browsers for smaller bundle
    target: 'es2020',
  },
});
