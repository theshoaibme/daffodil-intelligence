import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import {
  ApiError,
  deleteAccount as apiDeleteAccount,
  fetchCurrentUser,
  login as apiLogin,
  refreshAccessToken,
  register as apiRegister,
  registerUnauthorizedHandler,
  updateCurrentUser,
  type UserResponse,
  type UserUpdatePayload,
} from "@lib";
import {
  clearAuthSession,
  isTokenExpired,
  persistAuthSession,
  readStoredToken,
  readStoredUser,
  shouldRefreshToken,
} from "@lib";

export type AuthStatus = "loading" | "authenticated" | "unauthenticated" | "offline";

interface AuthContextValue {
  user: UserResponse | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  authStatus: AuthStatus;
  sessionError: string | null;
  login: (email: string, password: string) => Promise<void>;
  register: (data: { email: string; password: string; name?: string }) => Promise<void>;
  completeOAuth: (accessToken: string) => Promise<void>;
  logout: () => void;
  refreshSession: () => Promise<void>;
  updateProfile: (data: UserUpdatePayload) => Promise<UserResponse>;
  deleteAccount: (payload: { confirmation_phrase: string }) => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

const REFRESH_INTERVAL_MS = 20 * 60_000;

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [token, setToken] = useState<string | null>(() => readStoredToken());
  const [user, setUser] = useState<UserResponse | null>(() => readStoredUser<UserResponse>());
  const [authStatus, setAuthStatus] = useState<AuthStatus>(() =>
    readStoredToken() ? "loading" : "unauthenticated"
  );
  const [sessionError, setSessionError] = useState<string | null>(null);
  const validatingRef = useRef(false);

  const logout = useCallback(() => {
    clearAuthSession();
    setToken(null);
    setUser(null);
    setAuthStatus("unauthenticated");
    setSessionError(null);
  }, []);

  const applySession = useCallback((accessToken: string, profile: UserResponse) => {
    persistAuthSession(accessToken, profile);
    setToken(accessToken);
    setUser(profile);
    setAuthStatus("authenticated");
    setSessionError(null);
  }, []);

  const tryRefreshToken = useCallback(async (): Promise<string | null> => {
    try {
      const refreshed = await refreshAccessToken();
      return refreshed.access_token;
    } catch (error) {
      if (error instanceof ApiError && (error.status === 401 || error.status === 403)) {
        return null;
      }
      throw error;
    }
  }, []);

  const validateSession = useCallback(
    async (accessToken: string, options?: { allowOffline?: boolean }) => {
      if (validatingRef.current) return;
      validatingRef.current = true;

      try {
        // Persist immediately so authFetch reads the same token we are validating.
        const cachedUser = readStoredUser<UserResponse>();
        persistAuthSession(accessToken, cachedUser);
        setToken(accessToken);

        let activeToken = accessToken;

        if (isTokenExpired(activeToken) || shouldRefreshToken(activeToken)) {
          const refreshedToken = await tryRefreshToken();
          if (refreshedToken) {
            activeToken = refreshedToken;
            setToken(activeToken);
          } else if (isTokenExpired(activeToken)) {
            logout();
            setSessionError("Your session expired. Please sign in again.");
            return;
          }
        }

        try {
          const profile = await fetchCurrentUser();
          applySession(activeToken, profile);
        } catch (error) {
          if (error instanceof ApiError && (error.status === 401 || error.status === 403)) {
            const refreshedToken = await tryRefreshToken();
            if (refreshedToken) {
              const profile = await fetchCurrentUser();
              applySession(refreshedToken, profile);
              return;
            }

            logout();
            setSessionError("Your session expired. Please sign in again.");
            return;
          }

          if (options?.allowOffline !== false && cachedUser && activeToken) {
            setToken(activeToken);
            setUser(cachedUser);
            setAuthStatus("offline");
            setSessionError("Working offline. Could not verify your session.");
            return;
          }

          if (error instanceof ApiError) {
            setSessionError(error.message);
          } else {
            setSessionError("Unable to verify your session.");
          }
          logout();
        }
      } finally {
        validatingRef.current = false;
      }
    },
    [applySession, logout, tryRefreshToken]
  );

  const refreshSession = useCallback(async () => {
    const stored = readStoredToken();
    if (!stored || validatingRef.current) return;

    // Silent refresh when already signed in — avoids unmounting protected pages.
    setAuthStatus((prev) =>
      prev === "authenticated" || prev === "offline" ? prev : "loading"
    );
    await validateSession(stored, { allowOffline: true });
  }, [validateSession]);

  useEffect(() => {
    registerUnauthorizedHandler(() => {
      if (!readStoredToken() || validatingRef.current) return;
      logout();
      setSessionError("Your session expired. Please sign in again.");
    });
  }, [logout]);

  useEffect(() => {
    const stored = readStoredToken();
    if (!stored) {
      setAuthStatus("unauthenticated");
      return;
    }

    validateSession(stored, { allowOffline: true });
  }, [validateSession]);

  useEffect(() => {
    if (authStatus !== "authenticated" || !token) return;

    const interval = window.setInterval(() => {
      if (shouldRefreshToken(token)) {
        refreshSession();
      }
    }, REFRESH_INTERVAL_MS);

    return () => window.clearInterval(interval);
  }, [authStatus, token, refreshSession]);

  const login = useCallback(
    async (email: string, password: string) => {
      const { access_token } = await apiLogin(email, password);
      await validateSession(access_token, { allowOffline: false });
    },
    [validateSession]
  );

  const register = useCallback(
    async (data: { email: string; password: string; name?: string }) => {
      await apiRegister({
        email: data.email,
        password: data.password,
        full_name: data.name,
      });
      const { access_token } = await apiLogin(data.email, data.password);
      await validateSession(access_token, { allowOffline: false });
    },
    [validateSession]
  );

  const completeOAuth = useCallback(
    async (accessToken: string) => {
      await validateSession(accessToken, { allowOffline: false });
    },
    [validateSession]
  );

  const updateProfile = useCallback(
    async (data: UserUpdatePayload) => {
      const profile = await updateCurrentUser(data);
      const storedToken = readStoredToken();
      if (storedToken) {
        applySession(storedToken, profile);
      } else {
        setUser(profile);
      }
      return profile;
    },
    [applySession]
  );

  const deleteAccount = useCallback(
    async (payload: { confirmation_phrase: string }) => {
      await apiDeleteAccount(payload);
      logout();
    },
    [logout]
  );

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      token,
      isAuthenticated: authStatus === "authenticated" || authStatus === "offline",
      isLoading: authStatus === "loading",
      authStatus,
      sessionError,
      login,
      register,
      completeOAuth,
      logout,
      refreshSession,
      updateProfile,
      deleteAccount,
    }),
    [
      user,
      token,
      authStatus,
      sessionError,
      login,
      register,
      completeOAuth,
      logout,
      refreshSession,
      updateProfile,
      deleteAccount,
    ]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
