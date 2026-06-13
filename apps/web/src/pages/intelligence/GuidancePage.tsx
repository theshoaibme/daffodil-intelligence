import { useNavigate } from "react-router-dom";
import { GraduationCap, LogOut, MessageSquare } from "lucide-react";
import { useAuth } from "@context";
import { ROUTES } from "@lib";
import { Button } from "@ui";

export function GuidancePage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate(ROUTES.login, { replace: true });
  };

  return (
    <div className="min-h-screen bg-background text-on-surface font-sans">
      <header className="border-b border-outline-variant/40 bg-surface-container-lowest/80 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 h-14 flex items-center justify-between">
          <span className="font-medium text-lg">Guidance</span>
          <div className="flex items-center gap-3">
            <span className="hidden sm:inline text-sm text-on-surface-variant truncate max-w-[200px]">
              {user?.full_name || user?.email}
            </span>
            <Button variant="outlined" size="sm" onClick={handleLogout}>
              <LogOut size={16} className="mr-1.5" />
              Sign out
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 sm:px-6 py-10 sm:py-14">
        <div className="rounded-3xl border border-outline-variant/60 bg-surface-container-lowest p-6 sm:p-10">
          <div className="flex items-start gap-4 mb-6">
            <div className="p-3 rounded-2xl bg-primary/10 text-primary">
              <GraduationCap size={28} />
            </div>
            <div>
              <h1 className="text-2xl sm:text-3xl font-medium tracking-tight mb-2">
                Academic guidance
              </h1>
              <p className="text-on-surface-variant text-sm sm:text-base max-w-2xl">
                Welcome{user?.full_name ? `, ${user.full_name}` : ""}. This area is available after sign-in
                and will host personalized course planning, degree requirements, and advisor-style help.
              </p>
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-2 mt-8">
            <div className="rounded-2xl border border-outline-variant/40 bg-surface-container-low p-5">
              <MessageSquare size={20} className="text-primary mb-3" />
              <h2 className="font-medium mb-1">Ask about your program</h2>
              <p className="text-sm text-on-surface-variant">
                Open chat from the home dashboard for general academic questions.
              </p>
              <Button
                variant="tonal"
                size="sm"
                className="mt-4"
                onClick={() => navigate(ROUTES.home)}
              >
                Open chat
              </Button>
            </div>
            <div className="rounded-2xl border border-outline-variant/40 bg-surface-container-low p-5">
              <GraduationCap size={20} className="text-primary mb-3" />
              <h2 className="font-medium mb-1">Your profile</h2>
              <p className="text-sm text-on-surface-variant">
                {user?.department
                  ? `${user.department}${user.semester ? ` · Batch ${user.semester}` : ""}`
                  : "Complete your student profile to unlock tailored guidance."}
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
