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
      { find: /^@lib$/, replacement: resolve(__dirname, './src/lib/index.ts') },
      { find: /^@lib\//, replacement: resolve(__dirname, './src/lib') + '/' },
      { find: /^@hooks$/, replacement: resolve(__dirname, './src/hooks/index.ts') },
      { find: /^@context$/, replacement: resolve(__dirname, './src/context/index.ts') },
      { find: /^@styles$/, replacement: resolve(__dirname, './src/styles/index.ts') },
      { find: /^@ui$/, replacement: resolve(__dirname, './src/components/ui/index.ts') },
      { find: /^@pages$/, replacement: resolve(__dirname, './src/pages/index.ts') },
      { find: /^@providers$/, replacement: resolve(__dirname, './src/providers/index.ts') },
      { find: /^@auth$/, replacement: resolve(__dirname, './src/components/auth/index.ts') },
      { find: /^@auth\//, replacement: resolve(__dirname, './src/components/auth') + '/' },
      { find: /^@layout$/, replacement: resolve(__dirname, './src/components/layout/index.ts') },
      { find: /^@layout\//, replacement: resolve(__dirname, './src/components/layout') + '/' },
      { find: /^@features$/, replacement: resolve(__dirname, './src/components/features/index.ts') },
      { find: /^@features\//, replacement: resolve(__dirname, './src/components/features') + '/' },
      { find: /^@components\//, replacement: resolve(__dirname, './src/components') + '/' }
    ]
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