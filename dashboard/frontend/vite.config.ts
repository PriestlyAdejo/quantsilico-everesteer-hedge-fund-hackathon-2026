import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'node:path'

// Production Vite config for the exact Figma Research Console port.
// Figma Make kit plugins are not required for event-day builds.
export default defineConfig(({ mode }) => {
  const emitSourcemaps = mode === 'development'

  return {
    base: '/',
    build: {
      sourcemap: emitSourcemaps ? 'inline' : false,
      minify: !emitSourcemaps,
      chunkSizeWarningLimit: 1000,
    },
    plugins: [react(), tailwindcss()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
      },
    },
    server: {
      host: '127.0.0.1',
      port: parseInt(process.env.PORT || '8443'),
      strictPort: true,
      proxy: {
        '/api': {
          target: 'http://127.0.0.1:8766',
          changeOrigin: true,
        },
      },
    },
    preview: {
      host: '127.0.0.1',
      port: parseInt(process.env.PORT || '8443'),
    },
  }
})
