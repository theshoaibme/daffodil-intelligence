export const config = {
  API_URL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  WS_URL: import.meta.env.VITE_WS_URL || 'ws://localhost:8000',
  MCP_URL: import.meta.env.VITE_MCP_URL || 'http://localhost:8001',
};

export const AGENT_COLORS: Record<string, string> = {
  academic: '#6366f1',
  library: '#ec4899',
  campus: '#22c55e',
  career: '#f59e0b',
  coding: '#3b82f6',
  research: '#8b5cf6',
  wellness: '#06b6d4',
  finance: '#ef4444',
  vision: '#14b8a6',
  voice: '#f97316',
};

export const AGENT_ICONS: Record<string, string> = {
  academic: 'school',
  library: 'library_books',
  campus: 'directions_bus',
  career: 'work',
  coding: 'code',
  research: 'science',
  wellness: 'favorite',
  finance: 'account_balance',
  vision: 'visibility',
  voice: 'mic',
};