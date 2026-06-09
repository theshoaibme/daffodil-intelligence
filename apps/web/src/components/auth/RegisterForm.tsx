import React, { useState } from "react";
import { Link } from "react-router-dom";
import { Mail, Lock, User } from "lucide-react";
import { sendRegisterOtp, verifyRegisterOtp } from "@lib";
import { ROUTES } from "@lib";
import { Input, Button } from "../ui";

interface RegisterFormProps {
  onSuccess: (email: string) => void;
  disabled?: boolean;
}

export const RegisterForm: React.FC<RegisterFormProps> = ({ onSuccess, disabled = false }) => {
  const [step, setStep] = useState<"form" | "otp">("form");
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [acceptTerms, setAcceptTerms] = useState(false);
  const [otp, setOtp] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [devOtpHint, setDevOtpHint] = useState<string | null>(null);

  const handleSendOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!acceptTerms) {
      setError("You must accept the Terms of Service and Privacy Policy");
      return;
    }

    setLoading(true);
    setError(null);
    setDevOtpHint(null);
    try {
      const res = await sendRegisterOtp({
        first_name: firstName.trim(),
        last_name: lastName.trim(),
        email: email.trim(),
        password,
        accept_terms: acceptTerms,
      });
      setDevOtpHint(res.dev_otp ?? null);
      setStep("otp");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not send verification code");
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await verifyRegisterOtp({ email: email.trim(), code: otp.trim() });
      onSuccess(email.trim());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Verification failed");
    } finally {
      setLoading(false);
    }
  };

  const handleResend = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await sendRegisterOtp({
        first_name: firstName.trim(),
        last_name: lastName.trim(),
        email: email.trim(),
        password,
        accept_terms: true,
      });
      setDevOtpHint(res.dev_otp ?? null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not resend code");
    } finally {
      setLoading(false);
    }
  };

  if (step === "otp") {
    return (
      <form onSubmit={handleVerifyOtp} className="flex flex-col gap-4 w-full">
        <p className="text-sm text-on-surface-variant text-center">
          Enter the 6-digit code sent to{" "}
          <span className="font-medium text-on-surface">{email}</span>
        </p>

        {devOtpHint && (
          <p className="text-xs text-primary bg-primary/10 rounded-2xl px-4 py-2.5 text-center">
            Development OTP: <span className="font-mono font-semibold">{devOtpHint}</span>
          </p>
        )}

        <Input
          label="Verification code"
          type="text"
          inputMode="numeric"
          autoComplete="one-time-code"
          placeholder="000000"
          value={otp}
          onChange={(e) => setOtp(e.target.value.replace(/\D/g, "").slice(0, 6))}
          required
          minLength={6}
          maxLength={6}
        />

        {error && (
          <p className="text-sm text-error bg-error/10 rounded-2xl px-4 py-2.5" role="alert">
            {error}
          </p>
        )}

        <Button type="submit" size="lg" loading={loading} disabled={disabled || otp.length < 6} className="w-full mt-1">
          Verify &amp; create account
        </Button>

        <div className="flex items-center justify-between text-sm">
          <button
            type="button"
            onClick={() => {
              setStep("form");
              setOtp("");
              setError(null);
            }}
            className="text-on-surface-variant hover:text-on-surface border-0 bg-transparent cursor-pointer"
          >
            Back
          </button>
          <button
            type="button"
            onClick={handleResend}
            disabled={loading}
            className="text-primary font-medium hover:underline border-0 bg-transparent cursor-pointer disabled:opacity-50"
          >
            Resend code
          </button>
        </div>
      </form>
    );
  }

  return (
    <form onSubmit={handleSendOtp} className="flex flex-col gap-4 w-full">
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <Input
          label="First name"
          type="text"
          autoComplete="given-name"
          placeholder="First name"
          value={firstName}
          onChange={(e) => setFirstName(e.target.value)}
          required
          startIcon={<User size={18} />}
        />
        <Input
          label="Last name"
          type="text"
          autoComplete="family-name"
          placeholder="Last name"
          value={lastName}
          onChange={(e) => setLastName(e.target.value)}
          required
          startIcon={<User size={18} />}
        />
      </div>

      <Input
        label="Email"
        type="email"
        autoComplete="email"
        placeholder="you@daffodil.university"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        required
        startIcon={<Mail size={18} />}
      />

      <Input
        label="Password"
        type="password"
        autoComplete="new-password"
        placeholder="••••••••"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        required
        minLength={6}
        startIcon={<Lock size={18} />}
      />

      <label className="flex items-start gap-3 cursor-pointer select-none">
        <input
          type="checkbox"
          checked={acceptTerms}
          onChange={(e) => setAcceptTerms(e.target.checked)}
          className="mt-1 h-4 w-4 rounded border-outline-variant/50 text-primary focus:ring-primary/30 cursor-pointer"
        />
        <span className="text-sm text-on-surface-variant leading-relaxed">
          I accept the{" "}
          <Link to={ROUTES.terms} className="text-primary font-medium hover:underline" target="_blank" rel="noopener noreferrer">
            Terms of Service
          </Link>{" "}
          and{" "}
          <Link to={ROUTES.privacy} className="text-primary font-medium hover:underline" target="_blank" rel="noopener noreferrer">
            Privacy Policy
          </Link>
        </span>
      </label>

      {error && (
        <p className="text-sm text-error bg-error/10 rounded-2xl px-4 py-2.5" role="alert">
          {error}
        </p>
      )}

      <Button
        type="submit"
        size="lg"
        loading={loading}
        disabled={disabled || !acceptTerms}
        className="w-full mt-1"
      >
        Create account
      </Button>
    </form>
  );
};
