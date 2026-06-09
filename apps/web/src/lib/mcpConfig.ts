export interface LocalMcpServer {
  id: string;
  name: string;
  command: string;
}

const STORAGE_KEY = "di-mcp-local-servers";

export function readLocalMcpServers(): LocalMcpServer[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as LocalMcpServer[]) : [];
  } catch {
    return [];
  }
}

export function saveLocalMcpServers(servers: LocalMcpServer[]) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(servers));
}

export function hasLocalMcpServerName(name: string, excludeId?: string): boolean {
  const normalized = name.trim().toLowerCase();
  return readLocalMcpServers().some(
    (server) => server.id !== excludeId && server.name.trim().toLowerCase() === normalized
  );
}

export function addLocalMcpServer(name: string, command: string): LocalMcpServer[] {
  const trimmedName = name.trim();
  const trimmedCommand = command.trim();
  if (!trimmedName || !trimmedCommand) return readLocalMcpServers();
  if (hasLocalMcpServerName(trimmedName)) return readLocalMcpServers();

  const next: LocalMcpServer = {
    id: `local-${Date.now()}`,
    name: trimmedName,
    command: trimmedCommand,
  };
  const servers = [...readLocalMcpServers(), next];
  saveLocalMcpServers(servers);
  return servers;
}

export function removeLocalMcpServer(id: string): LocalMcpServer[] {
  const servers = readLocalMcpServers().filter((s) => s.id !== id);
  saveLocalMcpServers(servers);
  return servers;
}
