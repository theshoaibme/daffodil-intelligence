import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import { ROUTES } from "../../lib/routes";

export function AuthTelegramPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { completeOAuth } = useAuth();
  const [message, setMessage] = useState("Signing you in…");

  useEffect(() => {
    const token = searchParams.get("token");
    const error = searchParams.get("error");

    if (error) {
      setMessage("Sign-in failed. Return to Telegram and try again.");
      return;
    }

    if (!token) {
      setMessage("Missing sign-in token. Open the link from Telegram again.");
      return;
    }

    let cancelled = false;

    (async () => {
      try {
        await completeOAuth(token);
        if (!cancelled) navigate(ROUTES.home, { replace: true });
      } catch (err) {
        if (!cancelled) {
          setMessage(err instanceof Error ? err.message : "Sign-in failed.");
        }
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [navigate, searchParams, completeOAuth]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-background text-on-surface font-sans p-6">
      <div className="text-center max-w-md">
        <h1 className="text-2xl font-medium mb-3">Daffodil Intelligence</h1>
        <p className="text-on-surface-variant">{message}</p>
      </div>
    </div>
  );
}
