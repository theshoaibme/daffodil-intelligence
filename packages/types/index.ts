export interface User {
  id: number;
  email: string;
  full_name: string;
  student_id?: string;
  department?: string;
  semester?: number;
  role: 'student' | 'admin';
  cgpa?: number;
}

export interface Chat {
  id: number;
  title: string;
  agent_type: string;
  created_at: string;
}

export interface Message {
  id: number;
  chat_id: number;
  role: 'user' | 'assistant';
  content: string;
  metadata?: Record<string, any>;
  created_at: string;
}

export interface Agent {
  id: string;
  name: string;
  description: string;
  status: 'active' | 'ready' | 'busy';
  tools: string[];
}

export interface ToolResult {
  success: boolean;
  data?: any;
  error?: string;
}

export interface StreamChunk {
  type: 'text' | 'tool' | 'done';
  content: string;
  agent?: string;
}

export type AgentType =
  | 'supervisor'
  | 'academic'
  | 'library'
  | 'campus'
  | 'career'
  | 'coding'
  | 'research'
  | 'wellness'
  | 'finance'
  | 'vision'
  | 'voice';

export interface AgentRequest {
  message: string;
  agent_type: AgentType;
  chat_id?: number;
}

export interface AgentResponse {
  response: string;
  agent: string;
  tools_used: string[];
  sources: string[];
}