export interface ModelInfo {
  id: string;
  name: string;
  provider: string;
  isCustom?: boolean;
  apiUrl?: string;
  apiKey?: string;
}

/** Full catalog of built-in AI models available in the app. */
export const DEFAULT_MODELS: ModelInfo[] = [
  // Gemini
  { id: "gemini-2.5-flash", name: "Gemini 2.5 Flash", provider: "Gemini" },
  { id: "gemini-2.5-flash-lite", name: "Gemini 2.5 Flash Lite", provider: "Gemini" },
  { id: "gemini-2.5-pro", name: "Gemini 2.5 Pro", provider: "Gemini" },
  { id: "gemini-2.0-flash", name: "Gemini 2.0 Flash", provider: "Gemini" },
  { id: "gemini-2.0-flash-lite", name: "Gemini 2.0 Flash Lite", provider: "Gemini" },
  { id: "gemini-3-flash", name: "Gemini 3 Flash", provider: "Gemini" },
  { id: "gemini-3-pro", name: "Gemini 3 Pro", provider: "Gemini" },
  { id: "gemini-1.5-flash", name: "Gemini 1.5 Flash", provider: "Gemini" },
  { id: "gemini-1.5-pro", name: "Gemini 1.5 Pro", provider: "Gemini" },
  // OpenAI
  { id: "gpt-4o", name: "GPT-4o", provider: "OpenAI" },
  { id: "gpt-4o-mini", name: "GPT-4o mini", provider: "OpenAI" },
  { id: "gpt-4-turbo", name: "GPT-4 Turbo", provider: "OpenAI" },
  { id: "gpt-4", name: "GPT-4", provider: "OpenAI" },
  { id: "o1", name: "o1", provider: "OpenAI" },
  { id: "o1-mini", name: "o1 mini", provider: "OpenAI" },
  { id: "o3-mini", name: "o3 mini", provider: "OpenAI" },
  // Claude
  { id: "claude-3.5-sonnet", name: "Claude 3.5 Sonnet", provider: "Claude" },
  { id: "claude-3.5-haiku", name: "Claude 3.5 Haiku", provider: "Claude" },
  { id: "claude-3-opus", name: "Claude 3 Opus", provider: "Claude" },
  { id: "claude-3-sonnet", name: "Claude 3 Sonnet", provider: "Claude" },
  // DeepSeek
  { id: "deepseek-chat", name: "DeepSeek Chat", provider: "DeepSeek" },
  { id: "deepseek-reasoner", name: "DeepSeek Reasoner", provider: "DeepSeek" },
  // Meta / Mistral / Qwen
  { id: "llama-3.1-70b", name: "Llama 3.1 70B", provider: "Meta" },
  { id: "llama-3.1-8b", name: "Llama 3.1 8B", provider: "Meta" },
  { id: "mistral-large", name: "Mistral Large", provider: "Mistral" },
  { id: "qwen-2.5-72b", name: "Qwen 2.5 72B", provider: "Qwen" },
];

/** Models shown as nodes on the agent flow canvas. */
export const DASHBOARD_MODELS: ModelInfo[] = [
  { id: "gemini-2.0-flash", name: "Gemini 2.0 Flash", provider: "Gemini" },
  { id: "gemini-2.5-flash", name: "Gemini 2.5 Flash", provider: "Gemini" },
  { id: "gpt-4o", name: "GPT-4o", provider: "OpenAI" },
  { id: "claude-3.5-sonnet", name: "Claude 3.5 Sonnet", provider: "Claude" },
  { id: "deepseek-chat", name: "DeepSeek Chat", provider: "DeepSeek" },
];

const MODEL_BY_ID = new Map(DEFAULT_MODELS.map((m) => [m.id, m]));

export function getModels(): ModelInfo[] {
  try {
    const custom = localStorage.getItem("daffodil_custom_models");
    if (custom) {
      const parsed = JSON.parse(custom) as ModelInfo[];
      return [...DEFAULT_MODELS, ...parsed];
    }
  } catch (e) {
    console.error(e);
  }
  return DEFAULT_MODELS;
}

export function resolveModelName(modelId: string): string {
  const fromCatalog = MODEL_BY_ID.get(modelId);
  if (fromCatalog) return fromCatalog.name;
  const fromCustom = getModels().find((m) => m.id === modelId);
  if (fromCustom) return fromCustom.name;
  return modelId
    .replace(/gemini-/i, "Gemini ")
    .replace(/gpt-/i, "GPT-")
    .replace(/claude-/i, "Claude ")
    .replace(/-/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase())
    .trim();
}

export function modelNodeId(modelId: string): string {
  return `model-${modelId}`;
}
