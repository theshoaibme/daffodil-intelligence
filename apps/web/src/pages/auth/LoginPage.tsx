import React, { useMemo, useState } from "react";
import { Link, useLocation, useNavigate, useSearchParams } from "react-router-dom";
import { CredentialForm, GoogleAuthButton } from "@auth";
import { useAuth } from "@context";
import { AuthDivider, AuthLayout } from "@layout";
import { ROUTES } from "@lib";

interface LoginLocationState {
  registered?: boolean;
  email?: string;
  from?: string;
}

const GOOGLE_ERROR_MESSAGES: Record<string, string> = {
  access_denied: "Google sign-in was cancelled. Try again when you are ready.",
  oauth_failed: "Google sign-in could not be completed. Check API logs and OAuth redirect URIs.",
  invalid_token: "Google did not return a valid account email.",
  missing_code: "Google sign-in did not finish. Please try again.",
  service_unavailable: "Sign-in service is temporarily unavailable.",
};

export function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const [searchParams] = useSearchParams();
  const { login, isAuthenticated, sessionError } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const googleError = useMemo(() => {
    const code = searchParams.get("google_error");
    if (!code) return null;
    return GOOGLE_ERROR_MESSAGES[code] ?? "Google sign-in failed. Please try again.";
  }, [searchParams]);

  const state = location.state as LoginLocationState | null;
  const registrationSuccess = state?.registered;
  const registeredEmail = state?.email;
  const redirectTo = state?.from ?? ROUTES.home;

  React.useEffect(() => {
    if (isAuthenticated) navigate(redirectTo, { replace: true });
  }, [isAuthenticated, navigate, redirectTo]);

  const handleSubmit = async (data: { email: string; password: string }) => {
    setLoading(true);
    setError(null);
    try {
      await login(data.email, data.password);
      navigate(redirectTo, { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Sign in failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthLayout
      title="Sign in"
      footer={
        <>
          Don&apos;t have an account?{" "}
          <Link to={ROUTES.register} className="text-primary font-medium hover:underline">
            Create one
          </Link>
        </>
      }
    >
      {(googleError || sessionError) && (
        <p className="text-sm text-error bg-error/10 rounded-2xl px-4 py-2.5 mb-4 text-center" role="alert">
          {googleError ?? sessionError}
        </p>
      )}
      {registrationSuccess && (
        <p className="text-sm text-primary bg-primary/10 rounded-2xl px-4 py-2.5 mb-4 text-center" role="status">
          Account created{registeredEmail ? ` for ${registeredEmail}` : ""}. Sign in to continue.
        </p>
      )}
      <GoogleAuthButton disabled={loading} />
      <AuthDivider />
      <CredentialForm
        mode="login"
        onSubmit={handleSubmit}
        loading={loading}
        error={error}
        defaultEmail={registeredEmail ?? ""}
      />
    </AuthLayout>
  );
}
