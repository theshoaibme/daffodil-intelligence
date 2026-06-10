import { CheckCircle2, Info } from "lucide-react";
import { UiPanel } from "./UiPanel";

interface StatusCardProps {
  title?: string;
  tone?: string;
  message: string;
}

export function StatusCard({ title, tone = "info", message }: StatusCardProps) {
  const isSuccess = tone === "success";
  const Icon = isSuccess ? CheckCircle2 : Info;

  return (
    <UiPanel title={title}>
      <div className="flex items-start gap-2">
        <Icon
          size={16}
          className={isSuccess ? "text-primary mt-0.5 shrink-0" : "text-on-surface-variant mt-0.5 shrink-0"}
        />
        <p className="text-sm text-on-surface">{message}</p>
      </div>
    </UiPanel>
  );
}
