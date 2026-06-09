/** App route paths — public landing at `/`, product UI under `/intelligence` */
export const ROUTES = {
  landing: "/",
  home: "/intelligence",
  agents: "/intelligence/agents",
  skills: "/intelligence/skills",
  agentHub: "/intelligence/agent-hub",
  account: "/account",
  guidance: "/intelligence/guidance",
  login: "/login",
  register: "/register",
  terms: "/terms",
  privacy: "/privacy",
  live: "/intelligence/live",
  computer: "/intelligence/computer",
  model: "/intelligence/model",
  googleCallback: "/intelligence/auth/google/callback",
  telegramAuth: "/intelligence/auth/telegram",
} as const;

export type AppRoute = (typeof ROUTES)[keyof typeof ROUTES];
