import React from "react";
import { Shield, KeyRound, ArrowRight } from "lucide-react";

interface LoginPageProps {
  onLogin: () => void;
}

export function LoginPage({ onLogin }: LoginPageProps) {
  return (
    <div 
      className="flex flex-col items-center justify-center w-full h-full min-h-screen text-on-surface p-6 relative select-none"
      style={{
        background: "radial-gradient(circle at 50% 50%, var(--color-surface-container-low) 0%, var(--color-background) 100%)"
      }}
    >
      {/* Decorative Blur Orbs */}
      <div className="absolute top-1/4 left-1/4 w-72 h-72 bg-primary/10 rounded-full blur-[100px] pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 w-72 h-72 bg-secondary/15 rounded-full blur-[100px] pointer-events-none" />

      <div 
        className="w-full max-w-[400px] border border-outline-variant/50 rounded-[32px] p-8 shadow-2xl flex flex-col gap-6 items-center text-center backdrop-blur-xl pointer-events-auto"
        style={{
          backgroundColor: "color-mix(in srgb, var(--color-surface-container-lowest) 75%, transparent)"
        }}
      >
        {/* App Logo */}
        <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center text-primary shadow-inner border border-primary/20">
          <Shield size={32} className="animate-pulse" />
        </div>

        {/* Text */}
        <div className="flex flex-col gap-2">
          <h2 className="text-2xl font-bold tracking-tight">CopyCat Desktop</h2>
          <p className="text-sm text-on-surface-variant/80 px-2">
            AI-driven macro recording & playback companion. Please authenticate with your Daffodil Intelligence account to proceed.
          </p>
        </div>

        {/* Feature list */}
        <div className="w-full flex flex-col gap-3 py-2 text-left text-xs text-on-surface-variant">
          <div className="flex items-center gap-3 bg-surface-container/40 p-3 rounded-2xl border border-outline-variant/15">
            <KeyRound size={16} className="text-primary shrink-0" />
            <span>Secure single-sign-on (SSO) with your active web session</span>
          </div>
        </div>

        {/* Login Button */}
        <button
          onClick={onLogin}
          className="w-full py-4 px-6 rounded-full bg-primary text-on-primary font-semibold text-sm hover:bg-primary/95 transition-all shadow-lg hover:shadow-primary/25 flex items-center justify-center gap-2 group cursor-pointer"
        >
          <span>Authenticate with Web Dashboard</span>
          <ArrowRight size={16} className="transform transition-transform group-hover:translate-x-1" />
        </button>

        {/* Footer info */}
        <span className="text-[10px] text-on-surface-variant/60">
          Connection port: 3001 · Daemon online
        </span>
      </div>
    </div>
  );
}
