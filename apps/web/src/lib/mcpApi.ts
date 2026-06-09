import { getAuthHeaders } from "./api";

const API_BASE = import.meta.env.VITE_API_URL || "";

function apiUrl(path: string): string {
  const base = API_BASE.replace(/\/$/, "");
  return `${base}${path}`;
}

export interface McpServerSpec {
  name: string;
  command: string;
  args: string[];
  transport: string;
}

export interface McpStatusDetail {
  enabled: boolean;
  sdk_available: boolean;
  antigravity_available: boolean;
  configured: boolean;
  transport: string;
  server_count: number;
  servers: McpServerSpec[];
  local_tool_count: number;
  status: string;
}

export interface McpValidationResult {
  valid: boolean;
  errors: string[];
  spec?: McpServerSpec | null;
}

export interface McpServerTestResult {
  success: boolean;
  server_name: string;
  message: string;
  protocol_version?: string | null;
  server_name_reported?: string | null;
  tool_count: number;
  tools: string[];
  latency_ms: number;
  error?: string | null;
}

export interface McpUserServerEntry {
  name: string;
  command: string;
}

async function mcpFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(apiUrl(path), {
    ...init,
    headers: {
      ...getAuthHeaders(),
      ...(init?.headers ?? {}),
    },
  });

  if (!response.ok) {
    let detail = response.statusText;
    try {
      const data = await response.json();
      detail = typeof data.detail === "string" ? data.detail : detail;
    } catch {
      // ignore parse errors
    }
    throw new Error(detail || "MCP request failed");
  }

  return response.json() as Promise<T>;
}

export async function fetchMcpStatusDetail(): Promise<McpStatusDetail> {
  return mcpFetch<McpStatusDetail>("/api/mcp/status");
}

export async function fetchMcpUserServers(): Promise<{
  count: number;
  servers: McpUserServerEntry[];
}> {
  return mcpFetch("/api/mcp/user-servers");
}

export async function saveMcpUserServers(servers: McpUserServerEntry[]): Promise<{
  count: number;
  servers: McpUserServerEntry[];
}> {
  return mcpFetch("/api/mcp/user-servers", {
    method: "PUT",
    body: JSON.stringify({ servers }),
  });
}

export async function validateMcpServer(
  name: string,
  command: string
): Promise<McpValidationResult> {
  return mcpFetch<McpValidationResult>("/api/mcp/validate", {
    method: "POST",
    body: JSON.stringify({ name, command }),
  });
}

export async function testMcpServer(
  name: string,
  command: string,
  timeoutSeconds = 20
): Promise<McpServerTestResult> {
  return mcpFetch<McpServerTestResult>("/api/mcp/test", {
    method: "POST",
    body: JSON.stringify({ name, command, timeout_seconds: timeoutSeconds }),
  });
}

export async function testDaffodilMcpServer(timeoutSeconds = 25): Promise<McpServerTestResult> {
  return mcpFetch<McpServerTestResult>("/api/mcp/test", {
    method: "POST",
    body: JSON.stringify({ test_self: true, timeout_seconds: timeoutSeconds }),
  });
}

export function formatMcpCommand(spec: Pick<McpServerSpec, "command" | "args">): string {
  const parts = [spec.command, ...(spec.args ?? [])].filter(Boolean);
  return parts.join(" ");
}
