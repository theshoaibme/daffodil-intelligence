import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { fileURLToPath } from 'url'
import { dirname, resolve } from 'path'

const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@lib': resolve(__dirname, './src/lib/index.ts'),
      '@hooks': resolve(__dirname, './src/hooks/index.ts'),
      '@context': resolve(__dirname, './src/context/index.ts'),
      '@styles': resolve(__dirname, './src/styles/index.ts'),
      '@ui': resolve(__dirname, './src/components/ui/index.ts'),
      '@components': resolve(__dirname, './src/components')
    }
  },
  server: {
    port: 3000,
    proxy: {
      '/api': 'http://localhost:8000',
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true
      }
    }
  }
})