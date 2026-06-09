export interface AgentCapabilityInput {
  name: string;
  description: string;
  tools: string[];
}

export interface N8nImportResult {
  name: string;
  description: string;
  system_prompt: string;
  capabilities: AgentCapabilityInput[];
  category: string;
}

interface N8nNode {
  id?: string;
  name?: string;
  type?: string;
  parameters?: Record<string, unknown>;
}

interface N8nWorkflow {
  meta?: Record<string, unknown>;
  nodes?: N8nNode[];
  connections?: Record<string, unknown>;
}

const AGENT_NODE_RE = /langchain\.agent$/;
const TOOL_NODE_TYPES = new Set([
  "@n8n/n8n-nodes-langchain.toolHttpRequest",
  "n8n-nodes-base.httpRequest",
]);

function cleanN8nText(raw: unknown): string {
  if (typeof raw !== "string") return "";
  let text = raw.trim();
  if (text.startsWith("=")) text = text.slice(1).trim();
  return text
    .replace(/\{\{\s*\$json\.[^}]+\}\}/g, "[user input]")
    .replace(/\{\{\s*\$\([^)]+\)[^}]*\}\}/g, "[context]")
    .trim();
}

function inferCategory(nodes: N8nNode[]): string {
  const blob = nodes
    .map((n) => `${n.name || ""} ${n.type || ""} ${JSON.stringify(n.parameters || {})}`)
    .join(" ")
    .toLowerCase();
  if (/proxmox|vm|server|infra|api2|http/.test(blob)) return "computer";
  if (/research|paper|thesis/.test(blob)) return "productivity";
  if (/vision|image|camera/.test(blob)) return "ai";
  if (/plan|orchestrat|delegate/.test(blob)) return "orchestration";
  if (/academic|campus|university|student/.test(blob)) return "university";
  return "general";
}

function stickyDescription(nodes: N8nNode[]): string {
  const note = nodes.find((n) => n.type === "n8n-nodes-base.stickyNote");
  const content = cleanN8nText(note?.parameters?.content);
  if (!content) return "";
  const firstLine = content.split("\n").find((l) => l.trim() && !l.startsWith("#"));
  return firstLine?.replace(/^#+\s*/, "").trim().slice(0, 200) || "";
}

function toolCapability(node: N8nNode): AgentCapabilityInput {
  const params = node.parameters || {};
  const url = typeof params.url === "string" ? params.url : "";
  const desc =
    cleanN8nText(params.toolDescription) ||
    (url ? `HTTP tool: ${url}` : "Workflow tool integration");
  return {
    name: node.name || "Tool",
    description: desc,
    tools: url ? [url] : [],
  };
}

export function parseN8nWorkflow(raw: unknown): N8nImportResult {
  const workflow = raw as N8nWorkflow;
  if (!workflow || !Array.isArray(workflow.nodes)) {
    throw new Error("Invalid n8n workflow: missing nodes array");
  }

  const nodes = workflow.nodes;
  const agentNode =
    nodes.find((n) => AGENT_NODE_RE.test(n.type || "") && n.parameters?.text) ||
    nodes.find((n) => AGENT_NODE_RE.test(n.type || ""));

  const systemPrompt = cleanN8nText(agentNode?.parameters?.text);
  if (!systemPrompt) {
    throw new Error("No AI Agent system prompt found in workflow");
  }

  const capabilities = nodes
    .filter((n) => TOOL_NODE_TYPES.has(n.type || ""))
    .map(toolCapability)
    .filter((c, i, arr) => arr.findIndex((x) => x.name === c.name) === i);

  const name = agentNode?.name || "Imported n8n Agent";
  const description =
    stickyDescription(nodes) ||
    `Imported from n8n workflow (${capabilities.length} tool${capabilities.length === 1 ? "" : "s"})`;

  return {
    name,
    description,
    system_prompt: systemPrompt,
    capabilities: capabilities.length > 0 ? capabilities : [{ name: "workflow_tools", description: "Execute workflow-integrated tools", tools: [] }],
    category: inferCategory(nodes),
  };
}
