/**
 * Tool → agent mapping (keep in sync with apps/api/app/runtime/agent_simulation.py).
 */

export const PRODUCTIVITY_AGENT_IDS = [
  "coding",
  "research",
  "writing",
  "tasks",
] as const;

export const GENERAL_AGENT_IDS = ["event", "automation", "general"] as const;

const TOOL_AGENTS: Record<string, string[]> = {
  invoke_agent: ["planning", "automation"],
  parallel_invoke_agents: ["planning", "automation"],
  list_agents: ["planning", "automation"],
  create_automation_hook: ["event"],
  list_automation_hooks: ["event"],
  delete_automation_hook: ["event"],
  deep_research: ["research"],
  google_web_search: ["research"],
  web_search: ["research"],
  fetch_url: ["research"],
  search_papers: ["research"],
  get_citations: ["research"],
  run_shell_command: ["coding"],
  run_python: ["coding"],
  read_file: ["writing"],
  write_file: ["writing"],
  edit_file: ["writing"],
  list_directory: ["writing"],
  search_directory: ["writing"],
  find_file: ["writing"],
  delete_file: ["writing"],
  read_pdf: ["writing", "routine"],
  schedule_task: ["tasks"],
  get_daily_schedule: ["tasks", "event"],
  create_routine: ["tasks"],
  list_routines: ["tasks"],
  delete_routine: ["tasks"],
  create_reminder: ["event", "routine", "tasks"],
  list_reminders: ["event", "routine", "tasks"],
  delete_reminder: ["event", "routine", "tasks"],
  get_class_routine: ["routine"],
  read_routine_pdf: ["routine"],
  read_department_routine_pdf: ["routine"],
  enable_routine_automation: ["routine", "event"],
  send_telegram_message: ["event"],
  recall_notes: ["planning"],
  store_note: ["planning"],
  list_memories: ["planning"],
  take_screenshot: ["computer_use"],
  mouse_move: ["computer_use"],
  mouse_click: ["computer_use"],
  mouse_scroll: ["computer_use"],
  keyboard_type: ["computer_use"],
  keyboard_hotkey: ["computer_use"],
  start_recording: ["copycat"],
  stop_recording: ["copycat"],
  replay_recording: ["copycat"],
  get_cgpa: ["academic"],
  get_courses: ["academic"],
  get_attendance: ["academic"],
  get_exam_schedule: ["exam"],
  search_books: ["library"],
  get_book_availability: ["library"],
  get_shuttle_schedule: ["transport"],
  get_jobs: ["career"],
  get_internships: ["career"],
};

export function agentsForTool(toolName: string, invokeAgentId?: string): string[] {
  const key = (toolName || "").trim().toLowerCase();
  const found = new Set<string>(TOOL_AGENTS[key] ?? []);
  if (invokeAgentId) found.add(invokeAgentId.trim().toLowerCase());
  if (key.includes("research")) found.add("research");
  if (key.includes("routine") || key.includes("reminder")) {
    found.add("routine");
    found.add("tasks");
    found.add("event");
  }
  if (["read_pdf", "read_file", "write_file", "edit_file"].includes(key)) {
    found.add("writing");
  }
  if (key === "recall_notes" || key === "store_note" || key.startsWith("memory_")) {
    found.add("planning");
  }
  return Array.from(found);
}

export function isAgentActiveFromTools(agentId: string, activeTools: string[]): boolean {
  if (!activeTools.length) return false;
  return activeTools.some((tool) => agentsForTool(tool).includes(agentId));
}

export function agentsForActiveTools(activeTools: string[]): string[] {
  const ids = new Set<string>();
  for (const tool of activeTools) {
    for (const id of agentsForTool(tool)) ids.add(id);
  }
  return Array.from(ids);
}
