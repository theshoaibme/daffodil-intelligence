import React, { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { CredentialForm, GoogleAuthButton } from "../auth";
import { useAuth } from "@context";
import { AuthDivider, AuthLayout } from "./AuthLayout";
import { ROUTES } from "@lib";

interface LoginLocationState {
  registered?: boolean;
  email?: string;
  from?: string;
}

export function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { login, isAuthenticated, sessionError } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

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
      {sessionError && (
        <p className="text-sm text-error bg-error/10 rounded-2xl px-4 py-2.5 mb-4 text-center" role="alert">
          {sessionError}
        </p>
      )}
      {registrationSuccess && (
        <p className="text-sm text-primary bg-primary/10 rounded-2xl px-4 py-2.5 mb-4 text-center" role="status">
          Registration successful{registeredEmail ? ` for ${registeredEmail}` : ""}. Sign in with your credentials.
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
