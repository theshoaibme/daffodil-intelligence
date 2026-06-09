export interface LocalMcpServer {
  id: string;
  name: string;
  command: string;
}

const STORAGE_KEY = "di-local-mcp-servers";

export function readLocalMcpServers(): LocalMcpServer[] {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    return stored ? JSON.parse(stored) : [];
  } catch {
    return [];
  }
}

export function addLocalMcpServer(name: string, command: string): LocalMcpServer[] {
  const servers = readLocalMcpServers();
  const newServer: LocalMcpServer = {
    id: `mcp-${Date.now()}`,
    name: name.trim(),
    command: command.trim(),
  };
  const updated = [...servers, newServer];
  localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
  return updated;
}

export function removeLocalMcpServer(id: string): LocalMcpServer[] {
  const servers = readLocalMcpServers();
  const updated = servers.filter((s) => s.id !== id);
  localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
  return updated;
}
