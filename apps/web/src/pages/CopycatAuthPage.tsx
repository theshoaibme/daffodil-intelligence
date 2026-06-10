import { useEffect } from "react";
import { useAuth } from "@context";
import { useNavigate } from "react-router-dom";
import { Loader2 } from "lucide-react";
import { ROUTES } from "@lib";

export function CopycatAuthPage() {
  const { user, isAuthenticated, isLoading } = useAuth();
  const navigate = useNavigate();

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
      
      // Redirect to copycat companion app
      window.location.href = `http://localhost:3001/?token=${base64Token}`;
    } catch (err) {
      console.error("Failed to generate auth token for CopyCat", err);
    }
  }, [user, isAuthenticated, isLoading, navigate]);

  return (
    <div className="min-h-screen bg-background flex flex-col items-center justify-center text-on-surface">
      <div className="flex flex-col items-center gap-4 max-w-sm text-center px-4">
        <Loader2 className="w-10 h-10 animate-spin text-primary" />
        <h1 className="text-xl font-medium">Connecting to CopyCat</h1>
        <p className="text-sm text-on-surface-variant">
          Please wait while we authenticate your companion app...
        </p>
      </div>
    </div>
  );
}
