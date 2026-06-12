import React from "react";
import { Logo } from "../logo";

interface AuthLayoutProps {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
  footer?: React.ReactNode;
}

export const AuthLayout: React.FC<AuthLayoutProps> = ({ title, subtitle, children, footer }) => {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-background text-on-surface font-sans px-4 py-10 sm:px-6">
      <div className="w-full max-w-[420px]">
        <div className="text-center mb-8">
          <Logo size="lg" className="mx-auto" />
          {subtitle && (
            <p className="mt-2 text-sm text-on-surface-variant">{subtitle}</p>
          )}
        </div>

        <div className="rounded-3xl border border-outline-variant/60 bg-surface-container-lowest shadow-[0_4px_24px_rgba(26,27,36,0.06)] p-6 sm:p-8">
          <h1 className="text-xl sm:text-2xl font-medium mb-6 text-center">{title}</h1>
          {children}
        </div>

        {footer && <div className="mt-6 text-center text-sm text-on-surface-variant">{footer}</div>}
      </div>
    </div>
  );
};

export function AuthDivider() {
  return (
    <div className="flex items-center gap-3 my-2">
      <div className="flex-1 h-px bg-outline-variant/50" />
      <span className="text-xs text-on-surface-variant uppercase tracking-wide">or</span>
      <div className="flex-1 h-px bg-outline-variant/50" />
    </div>
  );
}
