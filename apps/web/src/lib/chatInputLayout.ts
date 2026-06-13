/**
 * Chat prompt bar width.
 * - Phone (<lg): full viewport minus horizontal gutters (sidebar hidden).
 * - sm+: floor 24rem (384px), cap at max-w-xl (576px).
 */
export const CHAT_INPUT_SHELL_CLASS =
  "w-full min-w-[calc(100vw-1.5rem)] max-w-[calc(100vw-1.5rem)] sm:min-w-[24rem] sm:max-w-xl";

/** Mobile task manager — narrower than chat input. */
export const MOBILE_TASK_PANEL_WIDTH_CLASS =
  "max-md:w-full max-md:max-w-[min(100%,calc(100vw-1.5rem-56px))] max-md:mx-auto";

/** Task manager on mobile — flat bottom corners, flush above input. */
export const MOBILE_TASK_PANEL_SHELL_CLASS =
  "max-md:rounded-t-3xl max-md:rounded-b-none max-md:border max-md:border-b-0 max-md:border-outline-variant/40 max-md:glass-gradient-panel max-md:shadow-md max-md:overflow-hidden";

/** Match chat input width on mobile only (keeps full input styling). */
export const MOBILE_INPUT_WIDTH_CLASS =
  "max-md:!min-w-[calc(100vw-1.5rem-20px)] max-md:!max-w-[calc(100vw-1.5rem-20px)]";
