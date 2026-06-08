import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import {
  fetchCurrentUser,
  login as apiLogin,
  register as apiRegister,
  type UserResponse,
} from "../lib/api";

const TOKEN_KEY = "di_access_token";
const USER_KEY = "di_user";
const EMAIL_KEY = "di_user_email";

interface AuthContextValue {
  user: UserResponse | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (data: { email: string; password: string; name?: string }) => Promise<void>;
  completeOAuth: (accessToken: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

function readStoredUser(): UserResponse | null {
  try {
    const raw = localStorage.getItem(USER_KEY);
    return raw ? (JSON.parse(raw) as UserResponse) : null;
  } catch {
    return null;
  }
}

function persistSession(token: string, user: UserResponse | null) {
  localStorage.setItem(TOKEN_KEY, token);
  if (user?.email) localStorage.setItem(EMAIL_KEY, user.email);
  if (user) localStorage.setItem(USER_KEY, JSON.stringify(user));
}

function clearSession() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
  localStorage.removeItem(EMAIL_KEY);
}

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(TOKEN_KEY));
  const [user, setUser] = useState<UserResponse | null>(() => readStoredUser());
  const [isLoading, setIsLoading] = useState(() => Boolean(localStorage.getItem(TOKEN_KEY)));

  const loadUser = useCallback(async (accessToken: string) => {
    localStorage.setItem(TOKEN_KEY, accessToken);
    setToken(accessToken);
    try {
      const profile = await fetchCurrentUser();
      setUser(profile);
      persistSession(accessToken, profile);
    } catch {
      clearSession();
      setToken(null);
      setUser(null);
    }
  }, []);

  useEffect(() => {
    const stored = localStorage.getItem(TOKEN_KEY);
    if (!stored) {
      setIsLoading(false);
      return;
    }
    loadUser(stored).finally(() => setIsLoading(false));
  }, [loadUser]);

  const login = useCallback(async (email: string, password: string) => {
    const { access_token } = await apiLogin(email, password);
    await loadUser(access_token);
  }, [loadUser]);

  const register = useCallback(async (data: { email: string; password: string; name?: string }) => {
    await apiRegister({
      email: data.email,
      password: data.password,
      full_name: data.name,
    });
    const { access_token } = await apiLogin(data.email, data.password);
    await loadUser(access_token);
  }, [loadUser]);

  const completeOAuth = useCallback(async (accessToken: string) => {
    await loadUser(accessToken);
  }, [loadUser]);

  const logout = useCallback(() => {
    clearSession();
    setToken(null);
    setUser(null);
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      token,
      isAuthenticated: Boolean(token && user),
      isLoading,
      login,
      register,
      completeOAuth,
      logout,
    }),
    [user, token, isLoading, login, register, completeOAuth, logout]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
