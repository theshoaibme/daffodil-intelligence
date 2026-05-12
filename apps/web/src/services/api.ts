const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

class ApiError extends Error {
  constructor(
    message: string,
    public statusCode?: number,
    public code?: string
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

class ApiService {
  private token: string | null = null

  getBaseUrl(): string {
    return API_URL
  }

  setToken(token: string | null) {
    this.token = token
    if (token) {
      localStorage.setItem('di_token', token)
    } else {
      localStorage.removeItem('di_token')
    }
  }

  getToken(): string | null {
    if (!this.token) {
      this.token = localStorage.getItem('di_token')
    }
    return this.token
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers
    }

    const token = this.getToken()
    if (token) {
      (headers as Record<string, string>)['Authorization'] = `Bearer ${token}`
    }

    const response = await fetch(`${API_URL}${endpoint}`, {
      ...options,
      headers
    })

    if (!response.ok) {
      let errorMessage = `API Error: ${response.status} ${response.statusText}`
      try {
        const errorData = await response.json()
        errorMessage = errorData.detail || errorData.message || errorMessage
      } catch {
        // Use default error message
      }
      throw new ApiError(errorMessage, response.status)
    }

    return response.json() as Promise<T>
  }

  async login(email: string, password: string) {
    const data = await this.request<{ access_token?: string; [key: string]: unknown }>('/api/auth/login-simple', {
      method: 'POST',
      body: JSON.stringify({ email, password })
    })
    if (data.access_token) {
      this.setToken(data.access_token)
    }
    return data
  }

  async register(name: string, email: string, password: string) {
    const data = await this.request<{ access_token?: string; [key: string]: unknown }>('/api/auth/register-simple', {
      method: 'POST',
      body: JSON.stringify({ name, email, password })
    })
    if (data.access_token) {
      this.setToken(data.access_token)
    }
    return data
  }

  async chat(message: string, _agentType: string = 'supervisor') {
    return this.request<{ response: string; agent?: string; [key: string]: unknown }>('/api/agents/test-chat', {
      method: 'POST',
      body: JSON.stringify({ message })
    })
  }

  async getUser() {
    return this.request<unknown>('/api/auth/me')
  }

  async getAgents() {
    return this.request<unknown>('/api/agents/list')
  }

  async getTools() {
    return this.request<unknown>('/api/agents/tools')
  }

  async analyzeImage(imageData: string) {
    return this.request<{ analysis?: string; error?: string; [key: string]: unknown }>('/api/agents/vision/analyze', {
      method: 'POST',
      body: JSON.stringify({ image: imageData })
    })
  }
}

export const api = new ApiService()
export { ApiError }