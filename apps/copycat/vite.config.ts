import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { fileURLToPath } from 'url'
import { dirname, resolve } from 'path'

const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)

export default defineConfig({
  base: './',
  plugins: [react()],
  resolve: {
    alias: {
      '@lib': resolve(__dirname, '../web/src/lib/index.ts'),
      '@hooks': resolve(__dirname, '../web/src/hooks/index.ts'),
      '@context': resolve(__dirname, '../web/src/context/index.ts'),
      '@styles': resolve(__dirname, '../web/src/styles/index.ts'),
      '@ui': resolve(__dirname, '../web/src/components/ui/index.ts'),
      '@features': resolve(__dirname, '../web/src/components/features/index.ts'),
      '@features/': resolve(__dirname, '../web/src/components/features') + '/',
      '@components/': resolve(__dirname, '../web/src/components') + '/'
    }
  },
  server: {
    port: 3001,
    proxy: {
      '/api': 'http://localhost:8000',
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true
      }
    }
  }
})
