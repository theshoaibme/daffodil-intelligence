import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { exchangeGoogleCode } from "../../lib/api";
import { useAuth } from "../../context/AuthContext";
import { googleRedirectUri } from "../auth/GoogleAuthButton";
import { ROUTES } from "../../lib/routes";
import { Loader } from "../ui";

export function GoogleCallbackPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { completeOAuth } = useAuth();
  const [message, setMessage] = useState("Completing Google sign-in…");

  useEffect(() => {
    const token = searchParams.get("token");
    const code = searchParams.get("code");
    const error = searchParams.get("error");

    if (error) {
      setMessage("Google sign-in was cancelled or denied. Return to login and try again.");
      return;
    }

    if (token) {
      let cancelled = false;
      (async () => {
        try {
          await completeOAuth(token);
          if (!cancelled) navigate(ROUTES.home, { replace: true });
        } catch (err) {
          if (!cancelled) {
            setMessage(err instanceof Error ? err.message : "Google sign-in failed.");
          }
        }
      })();
      return () => {
        cancelled = true;
      };
    }

    if (!code) {
      setMessage("Missing authorization code. Return to login and try again.");
      return;
    }

    let cancelled = false;

    (async () => {
      try {
        const result = await exchangeGoogleCode(code, googleRedirectUri());
        if (cancelled) return;
        await completeOAuth(result.access_token);
        navigate(ROUTES.home, { replace: true });
      } catch (err) {
        if (cancelled) return;
        setMessage(err instanceof Error ? err.message : "Google sign-in failed.");
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [searchParams, navigate, completeOAuth]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-background text-on-surface font-sans p-6">
      <div className="text-center max-w-md flex flex-col items-center gap-4">
        <Loader variant="spinner" diameter={28} strokeWidth={2.5} color="primary" />
        <h1 className="text-xl font-medium">Daffodil Intelligence</h1>
        <p className="text-on-surface-variant text-sm">{message}</p>
      </div>
    </div>
  );
}
