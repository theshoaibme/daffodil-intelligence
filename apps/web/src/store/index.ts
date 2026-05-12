import { create } from 'zustand'

interface User {
  id?: number
  email?: string
  full_name?: string
  student_id?: string
  department?: string
  semester?: number
  role?: string
  cgpa?: number
}

interface Message {
  id: number
  role: 'user' | 'assistant'
  content: string
  agent?: string
}

interface ChatState {
  messages: Message[]
  isLoading: boolean
  currentAgent: string
  setMessages: (msgs: Message[]) => void
  addMessage: (msg: Message) => void
  setLoading: (loading: boolean) => void
  setAgent: (agent: string) => void
  clear: () => void
}

export const useChatStore = create<ChatState>((set) => ({
  messages: [],
  isLoading: false,
  currentAgent: 'supervisor',
  setMessages: (messages) => set({ messages }),
  addMessage: (message) => set((state) => ({ messages: [...state.messages, message] })),
  setLoading: (isLoading) => set({ isLoading }),
  setAgent: (currentAgent) => set({ currentAgent }),
  clear: () => set({ messages: [], isLoading: false })
}))

interface AuthState {
  user: User | null
  token: string | null
  setUser: (user: User | null) => void
  setToken: (token: string | null) => void
  logout: () => void
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: localStorage.getItem('di_token'),
  setUser: (user) => set({ user }),
  setToken: (token) => set({ token }),
  logout: () => {
    localStorage.removeItem('di_token')
    set({ user: null, token: null })
  }
}))