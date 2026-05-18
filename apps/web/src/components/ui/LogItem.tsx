
import { CheckCircle2 } from "lucide-react";

export function LogItem({ text, active = false }: { text: string; active?: boolean }) {
  return (
    <div className={`flex items-start gap-3 p-2 rounded-lg ${active ? 'bg-primary/10 border border-primary/20' : 'bg-surface-container-highest/30'}`}>
      <CheckCircle2 size={18} className="text-primary mt-0.5 flex-shrink-0" />
      <span className={`text-sm ${active ? 'text-on-surface' : 'text-on-surface-variant'} font-medium line-clamp-1`}>{text}</span>
    </div>
  );
}
