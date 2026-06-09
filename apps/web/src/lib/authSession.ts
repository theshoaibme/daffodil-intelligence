const TOKEN_KEY = "di_access_token";
const USER_KEY = "di_user";
const EMAIL_KEY = "di_user_email";

export { TOKEN_KEY, USER_KEY, EMAIL_KEY };

export function readStoredToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function readStoredUser<T>(): T | null {
  try {
    const raw = localStorage.getItem(USER_KEY);
    return raw ? (JSON.parse(raw) as T) : null;
  } catch {
    return null;
  }
}

export function persistAuthSession(token: string, user: { email?: string } | null) {
  localStorage.setItem(TOKEN_KEY, token);
  if (user?.email) localStorage.setItem(EMAIL_KEY, user.email);
  if (user) localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function clearAuthSession() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
  localStorage.removeItem(EMAIL_KEY);
}

export function getTokenExpiryMs(token: string): number | null {
  try {
    const payload = token.split(".")[1];
    if (!payload) return null;
    const decoded = JSON.parse(atob(payload.replace(/-/g, "+").replace(/_/g, "/"))) as {
      exp?: number;
    };
    return typeof decoded.exp === "number" ? decoded.exp * 1000 : null;
  } catch {
    return null;
  }
}

export function isTokenExpired(token: string, skewMs = 30_000): boolean {
  const exp = getTokenExpiryMs(token);
  if (!exp) return false;
  return Date.now() + skewMs >= exp;
}

export function shouldRefreshToken(token: string, withinMs = 5 * 60_000): boolean {
  const exp = getTokenExpiryMs(token);
  if (!exp) return false;
  return exp - Date.now() <= withinMs;
}
