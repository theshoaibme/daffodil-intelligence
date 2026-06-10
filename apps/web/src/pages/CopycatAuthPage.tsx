import { useEffect, useState } from "react";
import { useAuth } from "@context";
import { useNavigate } from "react-router-dom";
import { Loader2, ArrowRight } from "lucide-react";
import { ROUTES } from "@lib";

export function CopycatAuthPage() {
  const { user, isAuthenticated, isLoading } = useAuth();
  const navigate = useNavigate();
  const [tokenLink, setTokenLink] = useState<string | null>(null);

  useEffect(() => {
    if (isLoading) return;

    if (!isAuthenticated || !user) {
      // Redirect to login page and preserve redirect path
      navigate(`${ROUTES.login}?redirect=${encodeURIComponent(ROUTES.copycat || "/copycat")}`, { replace: true });
      return;
    }

    // Prepare token payload
    const payload = {
      username: user.full_name || user.email.split("@")[0] || "User",
      email: user.email,
      image: user.avatar_url || "",
    };

    try {
      // Base64 encode using btoa and encodeURIComponent to handle unicode characters gracefully
      const base64Token = btoa(encodeURIComponent(JSON.stringify(payload)));
      const copycatUrl = import.meta.env.VITE_COPYCAT_URL || "http://localhost:3001";
      const redirectUrl = `${copycatUrl}/?token=${base64Token}`;
      setTokenLink(redirectUrl);

      // Auto-redirect after a short delay (1.5 seconds)
      const timer = setTimeout(() => {
        window.location.href = redirectUrl;
      }, 1500);

      return () => clearTimeout(timer);
    } catch (err) {
      console.error("Failed to generate auth token for CopyCat", err);
    }
  }, [user, isAuthenticated, isLoading, navigate]);

  return (
    <div className="min-h-screen bg-background flex flex-col items-center justify-center text-on-surface font-sans">
      <div className="flex flex-col items-center gap-6 max-w-sm text-center px-4">
        {tokenLink ? (
          <>
            <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center text-primary border border-primary/20 animate-bounce">
              <ArrowRight size={32} />
            </div>
            <h1 className="text-2xl font-bold tracking-tight">Connected Successfully</h1>
            <p className="text-sm text-on-surface-variant leading-relaxed">
              We are redirecting you back to the CopyCat companion app. If you are not redirected automatically, click the button below.
            </p>
            <a
              href={tokenLink}
              className="mt-2 px-6 py-3.5 rounded-full bg-primary text-on-primary font-semibold text-sm hover:opacity-95 active:scale-[0.99] transition-all shadow-lg hover:shadow-primary/25 flex items-center justify-center gap-2 border-0 cursor-pointer"
              style={{ backgroundColor: "var(--color-primary, #213be7)" }}
            >
              <span>Launch CopyCat</span>
              <ArrowRight size={16} />
            </a>
          </>
        ) : (
          <>
            <Loader2 className="w-12 h-12 animate-spin text-primary" />
            <h1 className="text-xl font-medium">Connecting to CopyCat</h1>
            <p className="text-sm text-on-surface-variant leading-relaxed">
              Please wait while we authenticate your companion app...
            </p>
          </>
        )}
      </div>
    </div>
  );
}
