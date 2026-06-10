import React, { createContext, useContext, useState, useEffect } from "react";

interface CopycatUser {
  username: string;
  email: string;
  image: string;
}

interface AuthContextType {
  isAuthenticated: boolean;
  user: CopycatUser | null;
  token: string | null;
  login: () => void;
  logout: () => void;
}

const CopycatAuthContext = createContext<AuthContextType | undefined>(undefined);

export function CopycatAuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem("copycat_token"));
  const [user, setUser] = useState<CopycatUser | null>(() => {
    const stored = localStorage.getItem("copycat_user");
    return stored ? JSON.parse(stored) : null;
  });

  // Extract token from URL query parameters on mount
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    let queryToken = params.get("token");

    if (!queryToken && window.location.hash.includes("?")) {
      const hashSearch = window.location.hash.split("?")[1];
      const hashParams = new URLSearchParams(hashSearch);
      queryToken = hashParams.get("token");
    }

    if (queryToken) {
      try {
        // Decode base64 JSON payload supporting unicode
        const decodedPayload = decodeURIComponent(atob(queryToken));
        const userData = JSON.parse(decodedPayload) as CopycatUser;

        localStorage.setItem("copycat_token", queryToken);
        localStorage.setItem("copycat_user", JSON.stringify(userData));

        setToken(queryToken);
        setUser(userData);

        // Clear token from URL bar cleanly
        const cleanUrl = window.location.origin + window.location.pathname + window.location.hash.split("?")[0];
        window.history.replaceState({}, document.title, cleanUrl);
      } catch (e) {
        console.error("Failed to parse auth token", e);
      }
    }
  }, []);

  const login = () => {
    // Redirect to web app copycat authentication bridge
    window.location.href = "http://localhost:3000/copycat";
  };

  const logout = () => {
    localStorage.removeItem("copycat_token");
    localStorage.removeItem("copycat_user");
    setToken(null);
    setUser(null);
  };

  return (
    <CopycatAuthContext.Provider
      value={{
        isAuthenticated: !!token,
        user,
        token,
        login,
        logout,
      }}
    >
      {children}
    </CopycatAuthContext.Provider>
  );
}

export function useCopycatAuth() {
  const context = useContext(CopycatAuthContext);
  if (!context) {
    throw new Error("useCopycatAuth must be used within a CopycatAuthProvider");
  }
  return context;
}
