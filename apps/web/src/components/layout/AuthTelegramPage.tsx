import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";

export function AuthTelegramPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
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

    localStorage.setItem("di_access_token", token);
    const email = searchParams.get("email");
    if (email) {
      localStorage.setItem("di_user_email", email);
    }
    setMessage("Signed in. Redirecting…");
    navigate("/", { replace: true });
  }, [navigate, searchParams]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-background text-on-surface font-sans p-6">
      <div className="text-center max-w-md">
        <h1 className="text-2xl font-medium mb-3">Daffodil Intelligence</h1>
        <p className="text-on-surface-variant">{message}</p>
      </div>
    </div>
  );
}
