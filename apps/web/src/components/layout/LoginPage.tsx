import React, { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { CredentialForm, GoogleAuthButton } from "../auth";
import { useAuth } from "../../context/AuthContext";
import { AuthDivider, AuthLayout } from "./AuthLayout";
import { ROUTES } from "../../lib/routes";

interface LoginLocationState {
  registered?: boolean;
  email?: string;
}

export function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { login, isAuthenticated } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const registrationSuccess = (location.state as LoginLocationState | null)?.registered;
  const registeredEmail = (location.state as LoginLocationState | null)?.email;

  React.useEffect(() => {
    if (isAuthenticated) navigate(ROUTES.home, { replace: true });
  }, [isAuthenticated, navigate]);

  const handleSubmit = async (data: { email: string; password: string }) => {
    setLoading(true);
    setError(null);
    try {
      await login(data.email, data.password);
      navigate(ROUTES.home, { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Sign in failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthLayout
      title="Sign in"
      subtitle="Access your academic guidance workspace"
      footer={
        <>
          Don&apos;t have an account?{" "}
          <Link to={ROUTES.register} className="text-primary font-medium hover:underline">
            Create one
          </Link>
        </>
      }
    >
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
