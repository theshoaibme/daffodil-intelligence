export const ICON_SIZE = 56;
export const ROOT_ICON_TOP = 16;
export const ROOT_ICON_CENTER = ROOT_ICON_TOP + ICON_SIZE / 2;

export const ROOT_DEFAULT_X = 480;
export const ROOT_DEFAULT_Y = 40;
export const ROOT_ICON_CENTER_Y = ROOT_DEFAULT_Y + ROOT_ICON_CENTER;
export const INPUT_NODE_X = 240;
export const INPUT_ICON_GAP = 124;
export const MODEL_NODE_Y = ROOT_DEFAULT_Y - 130;
export const MODEL_NODE_GAP = 108;

export function defaultInputY(index: number, total: number): number {
  const firstIconCenterY = ROOT_ICON_CENTER_Y - ((total - 1) * INPUT_ICON_GAP) / 2;
  return firstIconCenterY + index * INPUT_ICON_GAP - ICON_SIZE / 2;
}
