import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { GoogleAuthButton, RegisterForm } from "@auth";
import { useAuth } from "@context";
import { AuthDivider, AuthLayout } from "@layout";
import { ROUTES } from "@lib";

export function RegisterPage() {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();
  const [loading] = useState(false);

  React.useEffect(() => {
    if (isAuthenticated) navigate(ROUTES.home, { replace: true });
  }, [isAuthenticated, navigate]);

  const handleSuccess = (email: string) => {
    navigate(ROUTES.login, {
      replace: true,
      state: { registered: true, email },
    });
  };

  return (
    <AuthLayout
      title="Register"
      subtitle="Register for Daffodil Intelligence"
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
      <RegisterForm onSuccess={handleSuccess} disabled={loading} />
    </AuthLayout>
  );
}
