import { Link } from "react-router-dom";
import { BookOpen, MapPin, Shield } from "lucide-react";
import { Logo } from "@components/logo";
import { UserMenu } from "@layout";
import { useAuth } from "@context";
import { ROUTES } from "@lib";

const LANDING_WIDTH = "max-w-[90rem] mx-auto w-full px-5 sm:px-8 lg:px-10 xl:px-12";

const features = [
  {
    icon: BookOpen,
    title: "Study & career support",
    description: "Get help with academics, careers, coding, and library research in one place.",
  },
  {
    icon: MapPin,
    title: "Built for DIU",
    description: "Access courses, CGPA, fees, shuttle schedules, and other campus services.",
  },
  {
    icon: Shield,
    title: "Secure access",
    description: "Sign in with email or Google. Your workspace is private to you.",
  },
];

export function LandingPage() {
  const { isAuthenticated, isLoading } = useAuth();

  return (
    <div className="min-h-screen bg-background text-on-surface font-sans flex flex-col">
      <header className="sticky top-0 z-20 bg-surface-container-lowest/90 backdrop-blur-md">
        <div className={`${LANDING_WIDTH} h-16 sm:h-[4.25rem] flex items-center justify-between`}>
          <div className="flex items-center gap-6 sm:gap-10">
            <Logo size="md" />
            <nav className="hidden sm:flex items-center gap-5 sm:gap-7">
              <Link
                to={ROUTES.researchs}
                className="text-sm font-medium text-on-surface-variant hover:text-on-surface transition-colors"
              >
                Researchs
              </Link>
              <Link
                to={ROUTES.connections}
                className="text-sm font-medium text-on-surface-variant hover:text-on-surface transition-colors"
              >
                Connections
              </Link>
            </nav>
          </div>

          {!isLoading && (
            <nav className="flex items-center gap-2 sm:gap-4">
              {isAuthenticated ? (
                <UserMenu signOutRedirect={ROUTES.landing} showWorkspaceLink />
              ) : (
                <>
                  <Link
                    to={ROUTES.login}
                    className="px-4 py-2 text-sm font-medium text-on-surface-variant hover:text-on-surface rounded-xl transition-colors"
                  >
                    Sign in
                  </Link>
                  <Link
                    to={ROUTES.register}
                    className="px-5 py-2.5 text-sm font-medium bg-primary text-on-primary rounded-full hover:opacity-90 transition-opacity"
                  >
                    Get started
                  </Link>
                </>
              )}
            </nav>
          )}
        </div>
      </header>

      <main className="flex-1">
        <section className={`${LANDING_WIDTH} pt-16 sm:pt-20 lg:pt-28 pb-20 lg:pb-28 text-center`}>
          <h1 className="text-4xl sm:text-5xl lg:text-6xl xl:text-6xl font-medium tracking-tight leading-[1.08] max-w-4xl mx-auto mb-6 lg:mb-8">
            Your guide to campus life
          </h1>
          <p className="text-base sm:text-lg lg:text-xl text-on-surface-variant max-w-2xl mx-auto leading-relaxed">
            Study support, career guidance, and campus services — all in one workspace.
          </p>
        </section>

        <section className="bg-surface-container-low/50">
          <div className={`${LANDING_WIDTH} py-16 sm:py-20 lg:py-24`}>
            <div className="grid gap-6 sm:gap-8 lg:gap-10 sm:grid-cols-2 lg:grid-cols-3">
              {features.map(({ icon: Icon, title, description }) => (
                <div
                  key={title}
                  className="rounded-3xl bg-surface-container-lowest p-6 sm:p-8 text-left shadow-sm"
                >
                  <div className="w-11 h-11 sm:w-12 sm:h-12 rounded-2xl bg-primary/10 flex items-center justify-center mb-4 sm:mb-5">
                    <Icon size={22} className="text-primary" />
                  </div>
                  <h2 className="text-lg sm:text-xl font-medium mb-2">{title}</h2>
                  <p className="text-sm sm:text-base text-on-surface-variant leading-relaxed">{description}</p>
                </div>
              ))}
            </div>
          </div>
        </section>
      </main>

      <footer className="py-8 lg:py-10">
        <div className={`${LANDING_WIDTH} text-center text-sm text-on-surface-variant`}>
          <span>© {new Date().getFullYear()} Daffodil Intelligence</span>
        </div>
      </footer>
    </div>
  );
}
