import { motion } from "framer-motion";
import type { ReactNode } from "react";
import type { Card, CardStatus } from "../../engine/types";

const STATUS_STRIPE: Record<CardStatus, string> = {
  pending: "bg-on-surface-variant/30",
  active: "bg-primary",
  success: "bg-green-500",
  error: "bg-red-500",
  cancelled: "bg-on-surface-variant/20",
};

interface CardShellProps {
  card: Card;
  children: ReactNode;
  actions?: ReactNode;
}

export function CardShell({ card, children, actions }: CardShellProps) {
  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 4 }}
      animate={{ opacity: 1, y: 0 }}
      className="relative flex flex-col rounded-lg bg-surface-container-high/20 overflow-hidden"
    >
      <div className={`absolute left-0 top-0 bottom-0 w-0.5 ${STATUS_STRIPE[card.status]}`} />
      <div className="flex items-center justify-between gap-2 px-2.5 py-1.5">
        <div className="min-w-0 pl-1">
          <p className="text-xs font-medium text-on-surface truncate">{card.title}</p>
          {card.subtitle ? (
            <p className="text-[11px] text-on-surface-variant truncate">{card.subtitle}</p>
          ) : null}
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <span className="text-[10px] uppercase tracking-wide text-on-surface-variant/60">
            {card.status}
          </span>
          {actions}
        </div>
      </div>
      <div className="px-2.5 pb-2.5 pt-0 pl-3">{children}</div>
    </motion.div>
  );
}

export function CardSkeleton({ type: _type }: { type: string }) {
  return (
    <div className="rounded-lg bg-surface-container-high/25 p-3 animate-pulse">
      <div className="h-3.5 w-1/3 bg-outline-variant/15 rounded-sm mb-2" />
      <div className="h-3 w-full bg-outline-variant/10 rounded-sm mb-1.5" />
      <div className="h-3 w-2/3 bg-outline-variant/10 rounded-sm" />
    </div>
  );
}
