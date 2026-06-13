import type { CardType } from "../types";

export interface ToolRenderer {
  card_type: CardType;
  widget_type: string;
  icon: string;
}

const BUILTIN: Record<string, ToolRenderer> = {
  google_search: { card_type: "search", widget_type: "search_results", icon: "search" },
  web_search: { card_type: "search", widget_type: "search_results", icon: "search" },
  browser_navigate: { card_type: "browser", widget_type: "browser_session", icon: "globe" },
  shell_execute: { card_type: "terminal", widget_type: "terminal_output", icon: "terminal" },
  read_file: { card_type: "file", widget_type: "file_preview", icon: "file" },
  write_file: { card_type: "file", widget_type: "file_preview", icon: "file" },
  generate_image: { card_type: "image", widget_type: "image_gallery", icon: "image" },
  execute_code: { card_type: "code", widget_type: "code_viewer", icon: "code" },
};

function inferKind(toolName: string): CardType {
  const n = toolName.toLowerCase();
  if (n.includes("search")) return "search";
  if (n.includes("browser") || n.includes("navigate")) return "browser";
  if (n.includes("file") || n.includes("read") || n.includes("write")) return "file";
  if (n.includes("image")) return "image";
  if (n.includes("code") || n.includes("execute")) return "code";
  if (n.includes("shell") || n.includes("terminal")) return "terminal";
  if (n.includes("sql") || n.includes("database") || n.includes("query")) return "database";
  if (n.includes("chart") || n.includes("plot")) return "chart";
  if (n.includes("map")) return "map";
  if (n.includes("email") || n.includes("mail")) return "email";
  if (n.includes("calendar")) return "calendar";
  return "result";
}

export function resolveToolRenderer(
  toolName: string,
  mcpServer?: string
): ToolRenderer {
  const key = mcpServer ? `mcp:${mcpServer}:${toolName}` : toolName;
  if (BUILTIN[key]) return BUILTIN[key];
  if (BUILTIN[toolName]) return BUILTIN[toolName];

  const cardType = inferKind(toolName);
  return {
    card_type: cardType,
    widget_type: `${cardType}_widget`,
    icon: cardType,
  };
}

export function registerToolRenderer(key: string, renderer: ToolRenderer) {
  BUILTIN[key] = renderer;
}
