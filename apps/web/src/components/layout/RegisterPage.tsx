import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { CredentialForm, GoogleAuthButton } from "../auth";
import { useAuth } from "../../context/AuthContext";
import { AuthDivider, AuthLayout } from "./AuthLayout";
import { ROUTES } from "../../lib/routes";

export function RegisterPage() {
  const navigate = useNavigate();
  const { register, isAuthenticated } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  React.useEffect(() => {
    if (isAuthenticated) navigate(ROUTES.home, { replace: true });
  }, [isAuthenticated, navigate]);

  const handleSubmit = async (data: { email: string; password: string; name?: string }) => {
    setLoading(true);
    setError(null);
    try {
      await register(data);
      navigate(ROUTES.home, { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthLayout
      title="Create account"
      subtitle="Join Daffodil Intelligence"
      footer={
        <>
          Already have an account?{" "}
          <Link to={ROUTES.login} className="text-primary font-medium hover:underline">
            Sign in
          </Link>
        </>
      }
    >
      <GoogleAuthButton disabled={loading} />
      <AuthDivider />
      <CredentialForm mode="register" onSubmit={handleSubmit} loading={loading} error={error} />
    </AuthLayout>
  );
}
