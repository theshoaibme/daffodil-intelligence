/** Fallback descriptions when API returns an empty string. */
export const AGENT_DESCRIPTION_FALLBACKS: Record<string, string> = {
  academic: "Handles CGPA, results, courses, syllabus, and academic queries.",
  library: "Handles books, journals, PDFs, research papers, and library services.",
  campus: "Handles shuttle schedules, room bookings, notices, events, and campus facilities.",
  career: "Handles job opportunities, CV/resume help, career roadmap, and interview preparation.",
  coding: "Helps with code debugging, generation, explanation, and programming assistance.",
  research: "Helps with research papers, citations, thesis help, and literature review.",
  writing: "Drafts and edits documents, notes, PDFs, and files.",
  tasks: "Personal schedules, daily tasks, habits, and reminders.",
  wellness: "Mental health support, stress management, and study tips (non-medical advice only).",
  finance: "Handles tuition fees, payments, waivers, scholarships, and financial queries.",
  vision: "Analyzes images, PDFs, screenshots, and documents in real-time via camera.",
  voice: "Speech-to-text, text-to-speech, and live voice conversation.",
  exam: "Handles exam schedules, results, attendance, and academic calendar.",
  hostel: "Handles hostel bookings, room allocations, complaints, and facilities.",
  transport: "Handles shuttle schedules, routes, live tracking, and vehicle booking.",
  event: "Handles campus events, workshops, seminars, clubs, and activities.",
  complaint: "Handles student complaints, feedback, suggestions, and grievance resolution.",
  notification: "Handles notifications, announcements, alerts, and messaging preferences.",
  fee: "Handles tuition fees, payments, scholarships, waivers, and financial matters.",
  general: "Handles greetings, unknown queries, and basic clarification questions.",
  computer_use: "Controls mouse, keyboard, and screen for desktop automation tasks.",
  copycat: "Records and replays user actions for repeatable workflow automation.",
  planning: "Breaks down complex goals into plans and coordinates multi-step workflows.",
  routine: "Manages reminders, daily/weekly routines, schedules, and recurring task automation.",
};

export const ROOT_DESCRIPTION =
  "The main orchestrator that routes student requests to specialized agents, merges responses, and coordinates tools across the platform.";

export const CATEGORY_DESCRIPTIONS: Record<string, string> = {
  orchestration: "Plans tasks, delegates work, and coordinates multi-step workflows.",
  computer: "Screen control, browser automation, and recorded workflows.",
  productivity: "Coding, research, writing, tasks, notifications, and productivity tools.",
  university: "Campus services — academic, library, career, finance, routines, and more.",
  ai: "Vision, voice, and multimodal AI capabilities.",
  general: "Fallback agent for open-ended queries.",
};

export const CATEGORY_LABELS: Record<string, string> = {
  orchestration: "Orchestration",
  computer: "Computer Use",
  productivity: "Productivity",
  university: "University",
  ai: "AI & Vision",
  general: "General",
};

export function resolveAgentDescription(agentId: string, apiDescription?: string): string {
  const trimmed = (apiDescription || "").trim();
  if (trimmed) return trimmed;
  return AGENT_DESCRIPTION_FALLBACKS[agentId] ?? "Specialized agent for this domain.";
}
