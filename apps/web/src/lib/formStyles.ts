/** Shared form field styles — use `rounded` (1rem), not `rounded-xl` (3rem in this theme). */

export const FIELD_CLASS =
  "w-full px-3 py-2.5 rounded border border-outline-variant/40 bg-surface-container-lowest text-sm text-on-surface placeholder:text-on-surface-variant/60 outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/20 transition-colors";

export const FIELD_CLASS_COMPACT =
  "w-full px-3 py-2 rounded border border-outline-variant/40 bg-surface-container-lowest text-sm text-on-surface placeholder:text-on-surface-variant/60 outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/20 transition-colors";

/** Single-line fields — pill shape (name, description, category, etc.) */
export const FIELD_PILL_CLASS =
  "w-full px-4 py-2.5 rounded-full border border-outline-variant/40 bg-surface-container-lowest text-sm text-on-surface placeholder:text-on-surface-variant/60 outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/20 transition-colors";

export const TEXTAREA_CLASS = `${FIELD_CLASS} resize-y leading-relaxed`;

export const SELECT_CLASS = FIELD_CLASS_COMPACT;

export const SELECT_PILL_CLASS = FIELD_PILL_CLASS;

export const FIELD_LABEL_CLASS = "block text-xs font-medium text-on-surface-variant mb-1.5";
