import { Settings } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import { ROUTES } from "../../lib/routes";

export function SettingsPage() {
  const navigate = useNavigate();
  const { user, isAuthenticated, logout } = useAuth();

  return (
    <div className="min-h-screen bg-background text-on-surface font-sans">
      <div className="max-w-lg mx-auto px-6 py-12">
        <button
          type="button"
          onClick={() => navigate(ROUTES.home)}
          className="text-sm text-primary hover:underline mb-6"
        >
          ← Back to workspace
        </button>

        <div className="flex items-center gap-3 mb-8">
          <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center">
            <Settings size={20} className="text-primary" />
          </div>
          <div>
            <h1 className="text-xl font-semibold">Settings</h1>
            <p className="text-sm text-on-surface-variant">Account and preferences</p>
          </div>
        </div>

        <div className="rounded-2xl border border-outline-variant bg-surface-container-lowest p-6 space-y-4">
          {isAuthenticated && user ? (
            <>
              <div>
                <p className="text-xs uppercase tracking-wider text-on-surface-variant font-bold mb-1">
                  Signed in as
                </p>
                <p className="text-sm font-medium">{user.full_name || user.email}</p>
                <p className="text-sm text-on-surface-variant">{user.email}</p>
              </div>
              <button
                type="button"
                onClick={() => {
                  logout();
                  navigate(ROUTES.login);
                }}
                className="w-full py-2.5 rounded-xl border border-outline-variant text-sm font-medium hover:bg-surface-container-high transition-colors"
              >
                Sign out
              </button>
            </>
          ) : (
            <div className="flex flex-col gap-2">
              <button
                type="button"
                onClick={() => navigate(ROUTES.login)}
                className="w-full py-2.5 rounded-xl bg-primary text-on-primary text-sm font-medium"
              >
                Sign in
              </button>
              <button
                type="button"
                onClick={() => navigate(ROUTES.register)}
                className="w-full py-2.5 rounded-xl border border-outline-variant text-sm font-medium hover:bg-surface-container-high"
              >
                Create account
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
