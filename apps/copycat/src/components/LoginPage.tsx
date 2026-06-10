import React from "react";
import { Shield, ArrowRight, ShieldCheck } from "lucide-react";

interface LoginPageProps {
  onLogin: () => void;
}

export function LoginPage({ onLogin }: LoginPageProps) {
  const handleOpenTerms = (e: React.MouseEvent) => {
    e.preventDefault();
    const url = "http://localhost:3000/terms";
    const api = window.electronAPI as any;
    if (api?.openExternal) {
      api.openExternal(url);
    } else {
      window.open(url, "_blank");
    }
  };

  const handleOpenPrivacy = (e: React.MouseEvent) => {
    e.preventDefault();
    const url = "http://localhost:3000/privacy";
    const api = window.electronAPI as any;
    if (api?.openExternal) {
      api.openExternal(url);
    } else {
      window.open(url, "_blank");
    }
  };

  return (
    <div 
      className="flex flex-col items-center justify-center w-full h-full min-h-screen text-on-surface p-6 relative select-none"
      style={{
        background: "radial-gradient(circle at 50% 50%, var(--color-surface-container-low, #eeecfa) 0%, var(--color-background, #fbf8ff) 100%)",
        fontFamily: "'Roboto Flex', system-ui, -apple-system, sans-serif"
      }}
    >
      {/* Premium Glassmorphic Ambient Orbs */}
      <div className="absolute top-1/4 left-1/4 w-80 h-80 bg-primary/10 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-secondary/15 rounded-full blur-[120px] pointer-events-none" />

      {/* Main Single Dialog Container */}
      <div 
        className="w-full max-w-[420px] border border-outline-variant/60 rounded-[48px] p-8 sm:p-10 shadow-2xl flex flex-col gap-8 items-center text-center backdrop-blur-2xl pointer-events-auto transition-all duration-300 hover:shadow-primary/5"
        style={{
          backgroundColor: "rgba(255, 255, 255, 0.85)"
        }}
      >
        {/* App Logo */}
        <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center text-primary border border-primary/20 shadow-inner">
          <Shield size={32} className="animate-pulse" />
        </div>

        {/* Dynamic Typography Header */}
        <div className="flex flex-col gap-2">
          <h2 className="text-2xl font-bold tracking-tight text-on-surface">CopyCat Desktop</h2>
          <p className="text-sm text-on-surface-variant leading-relaxed">
            Secure Single Sign-on
          </p>
        </div>

        {/* Feature Highlights */}
        <div className="w-full flex items-center gap-3 bg-surface-container/60 p-4 rounded-[20px] border border-outline-variant/30 text-left text-xs text-on-surface-variant leading-relaxed">
          <ShieldCheck size={18} className="text-primary shrink-0" />
          <span>Authenticate instantly using your active web dashboard session.</span>
        </div>

        {/* Action Button Group */}
        <div className="w-full flex flex-col gap-3">
          <button
            onClick={onLogin}
            className="w-full py-4 px-6 rounded-full bg-primary text-on-primary font-semibold text-sm hover:opacity-95 active:scale-[0.99] transition-all shadow-lg hover:shadow-primary/25 flex items-center justify-center gap-2 group cursor-pointer border-0"
            style={{ backgroundColor: "var(--color-primary, #213be7)" }}
          >
            <span>Login to Workspace</span>
            <ArrowRight size={16} className="transform transition-transform group-hover:translate-x-1" />
          </button>
        </div>

        {/* Terms & Conditions Footer Links */}
        <div className="flex flex-wrap items-center justify-center gap-2 text-[11px] text-on-surface-variant/70 mt-2">
          <a 
            href="http://localhost:3000/terms" 
            onClick={handleOpenTerms}
            className="hover:text-primary transition-colors hover:underline"
          >
            Terms of Service
          </a>
          <span>·</span>
          <a 
            href="http://localhost:3000/privacy" 
            onClick={handleOpenPrivacy}
            className="hover:text-primary transition-colors hover:underline"
          >
            Privacy Policy
          </a>
        </div>
      </div>
    </div>
  );
}
