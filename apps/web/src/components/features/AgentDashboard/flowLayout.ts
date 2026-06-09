export type SavedPositions = Record<string, { x: number; y: number }>;

export const ICON_SIZE = 48;
export const ROOT_BORDER = 2;
export const ROOT_PADDING_Y = 8;
export const ROOT_ICON_SIZE = ICON_SIZE;
export const ROOT_LABEL_GAP = 4;
export const ROOT_LABEL_LINE = 16;
export const ROOT_CARD_HEIGHT =
  ROOT_BORDER * 2 + ROOT_PADDING_Y * 2 + ROOT_ICON_SIZE + ROOT_LABEL_GAP + ROOT_LABEL_LINE;
export const ROOT_CARD_CENTER = ROOT_CARD_HEIGHT / 2;
/** Vertical center of the brain icon — left/right inputs and response connect here. */
export const ROOT_HUB_Y = ROOT_BORDER + ROOT_PADDING_Y + ROOT_ICON_SIZE / 2;
/** Top of the brain icon — AI model nodes connect here. */
export const ROOT_HUB_TOP = ROOT_BORDER + ROOT_PADDING_Y;

/** Horizontal anchor for the orchestrator — categories fan out from here. */
export const ROOT_DEFAULT_X = 480;
/** Keeps model row above the root in positive Y space. */
export const ROOT_DEFAULT_Y = 64;
export const INPUT_OFFSET_X = 200;
export const OUTPUT_OFFSET_X = 200;
export const CATEGORY_ROW_OFFSET_Y = 140;
export const AGENT_ROW_OFFSET_Y = 260;
export const CATEGORY_COL_GAP = 168;
export const AGENT_COL_GAP = 88;
export const INPUT_ICON_GAP = 96;
export const ROOT_CARD_MIN_WIDTH = 180;
export const MODEL_NODE_GAP = 80;
export const MODEL_EDGE_GAP = 20;

export const FLOW_FIT_OPTIONS = { padding: 0.14, maxZoom: 1.15, duration: 240 } as const;

export function sideNodeY(index: number, total: number, rootY: number): number {
  const hubCenterY = rootY + ROOT_HUB_Y;
  const firstIconCenterY = hubCenterY - ((total - 1) * INPUT_ICON_GAP) / 2;
  return firstIconCenterY + index * INPUT_ICON_GAP - ICON_SIZE / 2;
}

export function modelNodeY(rootY: number): number {
  return rootY + ROOT_HUB_TOP - ICON_SIZE - MODEL_EDGE_GAP;
}

export function modelNodeX(index: number, total: number, rootX: number): number {
  const span = Math.max(total - 1, 0) * MODEL_NODE_GAP;
  const cardCenterX = rootX + ROOT_CARD_MIN_WIDTH / 2;
  const firstCenterX = cardCenterX - span / 2;
  return firstCenterX + index * MODEL_NODE_GAP - ICON_SIZE / 2;
}
