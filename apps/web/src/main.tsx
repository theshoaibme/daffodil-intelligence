import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App'
import { ThemeProvider } from '@providers'
import { QueryProvider } from './providers/QueryProvider'
import { ConfigProvider } from "@context"
import { AuthProvider } from "@context"
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <ThemeProvider>
        <ConfigProvider>
          <AuthProvider>
            <QueryProvider>
              <App />
            </QueryProvider>
          </AuthProvider>
        </ConfigProvider>
      </ThemeProvider>
    </BrowserRouter>
  </React.StrictMode>
)