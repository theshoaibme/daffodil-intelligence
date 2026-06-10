import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { fileURLToPath } from 'url'
import { dirname, resolve } from 'path'

const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: [
      { find: /^@lib$/, replacement: resolve(__dirname, '../web/src/lib/index.ts') },
      { find: /^@hooks$/, replacement: resolve(__dirname, '../web/src/hooks/index.ts') },
      { find: /^@context$/, replacement: resolve(__dirname, '../web/src/context/index.ts') },
      { find: /^@styles$/, replacement: resolve(__dirname, '../web/src/styles/index.ts') },
      { find: /^@ui$/, replacement: resolve(__dirname, '../web/src/components/ui/index.ts') },
      { find: /^@features$/, replacement: resolve(__dirname, '../web/src/components/features/index.ts') },
      { find: /^@features\//, replacement: resolve(__dirname, '../web/src/components/features') + '/' },
      { find: /^@components\//, replacement: resolve(__dirname, '../web/src/components') + '/' }
    ]
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
