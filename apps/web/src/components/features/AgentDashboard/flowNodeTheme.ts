export interface NodeTheme {
  bg: string;
  text: string;
  border: string;
  iconBg: string;
}

export const CATEGORY_NODE_THEME: Record<string, NodeTheme> = {
  university: {
    bg: "bg-primary/10",
    text: "text-primary",
    border: "border-primary/30",
    iconBg: "bg-primary/10",
  },
  computer: {
    bg: "bg-primary/10",
    text: "text-primary",
    border: "border-primary/25",
    iconBg: "bg-primary/10",
  },
  orchestration: {
    bg: "bg-surface-container-high",
    text: "text-primary",
    border: "border-primary/20",
    iconBg: "bg-primary/15",
  },
  productivity: {
    bg: "bg-surface-container",
    text: "text-on-surface",
    border: "border-outline-variant/35",
    iconBg: "bg-surface-container-high",
  },
  ai: {
    bg: "bg-primary/15",
    text: "text-primary",
    border: "border-primary/30",
    iconBg: "bg-primary/10",
  },
  general: {
    bg: "bg-surface-container",
    text: "text-on-surface-variant",
    border: "border-outline-variant/35",
    iconBg: "bg-surface-container-high",
  },
};

export const DEFAULT_NODE_THEME: NodeTheme = {
  bg: "bg-surface-container-lowest",
  text: "text-on-surface",
  border: "border-outline-variant",
  iconBg: "bg-surface-container-lowest",
};

export const MODEL_NODE_THEME: NodeTheme = {
  bg: "bg-surface-container-lowest",
  text: "text-on-surface",
  border: "border-outline-variant",
  iconBg: "bg-surface-container-lowest",
};

export const ROOT_NODE_THEME: NodeTheme = {
  bg: "bg-surface-container-lowest",
  text: "text-on-surface",
  border: "border-outline-variant",
  iconBg: "bg-surface-container-low",
};

export const RESPONSE_NODE_THEME: NodeTheme = {
  bg: "bg-emerald-500/10",
  text: "text-emerald-700",
  border: "border-emerald-500/30",
  iconBg: "bg-emerald-500/15",
};

export const MEMORY_NODE_THEME: NodeTheme = {
  bg: "bg-violet-500/10",
  text: "text-violet-700",
  border: "border-violet-500/30",
  iconBg: "bg-violet-500/15",
};

export const INTEGRATION_NODE_THEME: Record<string, NodeTheme> = {
  telegram: {
    bg: "bg-surface-container-high",
    text: "text-on-surface",
    border: "border-outline-variant/40",
    iconBg: "bg-surface-container-high",
  },
  chat: {
    bg: "bg-surface-container",
    text: "text-on-surface",
    border: "border-outline-variant/40",
    iconBg: "bg-surface-container",
  },
};

export function getCategoryTheme(category = "general"): NodeTheme {
  return CATEGORY_NODE_THEME[category] ?? CATEGORY_NODE_THEME.general;
}

export function getIntegrationTheme(integration = "chat"): NodeTheme {
  return INTEGRATION_NODE_THEME[integration] ?? INTEGRATION_NODE_THEME.chat;
}

export const NODE_RING_OFFSET = "ring-offset-surface-low";
