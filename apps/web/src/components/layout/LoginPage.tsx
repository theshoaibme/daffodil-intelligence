import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { CredentialForm, GoogleAuthButton } from "../auth";
import { useAuth } from "../../context/AuthContext";
import { AuthDivider, AuthLayout } from "./AuthLayout";
import { ROUTES } from "../../lib/routes";

export function LoginPage() {
  const navigate = useNavigate();
  const { login, isAuthenticated } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

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
      <GoogleAuthButton disabled={loading} />
      <AuthDivider />
      <CredentialForm mode="login" onSubmit={handleSubmit} loading={loading} error={error} />
    </AuthLayout>
  );
}
