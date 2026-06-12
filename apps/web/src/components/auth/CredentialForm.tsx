import React, { useState } from "react";
import { Mail, Lock, User } from "lucide-react";
import { Input, Button } from "../ui";

export interface CredentialFormData {
  email: string;
  password: string;
  name?: string;
}

interface CredentialFormProps {
  mode: "login" | "register";
  onSubmit: (data: CredentialFormData) => Promise<void>;
  loading?: boolean;
  error?: string | null;
  submitLabel?: string;
  defaultEmail?: string;
}

export const CredentialForm: React.FC<CredentialFormProps> = ({
  mode,
  onSubmit,
  loading = false,
  error,
  submitLabel,
  defaultEmail = "",
}) => {
  const [email, setEmail] = useState(defaultEmail);
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await onSubmit({
      email: email.trim(),
      password,
      ...(mode === "register" ? { name: name.trim() || undefined } : {}),
    });
  };

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4 w-full">
      {mode === "register" && (
        <Input
          label="Full name"
          type="text"
          autoComplete="name"
          placeholder="Enter full name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          startIcon={<User size={18} />}
        />
      )}

      <Input
        label="Email"
        type="email"
        autoComplete="email"
        placeholder="Enter email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        required
        startIcon={<Mail size={18} />}
      />

      <Input
        label="Password"
        type="password"
        autoComplete={mode === "login" ? "current-password" : "new-password"}
        placeholder="Enter password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        required
        minLength={6}
        startIcon={<Lock size={18} />}
      />

      {error && (
        <p className="text-sm text-error bg-error/10 rounded-2xl px-4 py-2.5" role="alert">
          {error}
        </p>
      )}

      <Button type="submit" size="lg" loading={loading} className="w-full mt-1">
        {submitLabel ?? (mode === "login" ? "Sign in" : "Create account")}
      </Button>
    </form>
  );
};
