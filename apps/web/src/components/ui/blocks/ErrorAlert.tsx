import { AlertCircle } from "lucide-react";
import { UiPanel } from "./UiPanel";

interface ErrorAlertProps {
  title?: string;
  message: string;
}

export function ErrorAlert({ title, message }: ErrorAlertProps) {
  return (
    <UiPanel title={title}>
      <div className="flex items-start gap-2 text-error">
        <AlertCircle size={16} className="mt-0.5 shrink-0" />
        <p className="text-sm">{message}</p>
      </div>
    </UiPanel>
  );
}
