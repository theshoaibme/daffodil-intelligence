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
      '@auth': resolve(__dirname, './src/components/auth'),
      '@layout': resolve(__dirname, './src/components/layout'),
      '@features': resolve(__dirname, './src/components/features'),
      '@pages': resolve(__dirname, './src/pages'),
      '@providers': resolve(__dirname, './src/providers'),
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