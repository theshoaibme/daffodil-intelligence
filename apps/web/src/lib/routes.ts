/** App route paths — public landing at `/`, product UI under `/studio` */
export const STUDIO_PATH_PREFIX = "/studio";

export const ROUTES = {
  landing: "/",
  home: "/studio",
  agents: "/studio/agents",
  skills: "/studio/skills",
  agentHub: "/studio/agent-hub",
  account: "/account",
  guidance: "/studio/guidance",
  login: "/login",
  register: "/register",
  terms: "/terms",
  privacy: "/privacy",
  live: "/studio/live",
  computer: "/studio/computer",
  model: "/studio/model",
  googleCallback: "/studio/auth/google/callback",
  telegramAuth: "/studio/auth/telegram",
  copycat: "/copycat",
  researchs: "/studio/researchs",
  researchPaper: "/studio/researchs/:paperId",
  publicResearchs: "/researchs",
  publicResearchPaper: "/researchs/:paperId",
  connections: "/connections",
} as const;

export type AppRoute = (typeof ROUTES)[keyof typeof ROUTES];

export function isStudioPath(pathname: string): boolean {
  return pathname === STUDIO_PATH_PREFIX || pathname.startsWith(`${STUDIO_PATH_PREFIX}/`);
}

export function researchPaperPath(
  paperId: string,
  opts?: { workspace?: boolean },
): string {
  const pattern = opts?.workspace ? ROUTES.researchPaper : ROUTES.publicResearchPaper;
  return pattern.replace(":paperId", encodeURIComponent(paperId));
}
