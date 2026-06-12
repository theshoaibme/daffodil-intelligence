import { Link } from "react-router-dom";
import {
  ArrowRight,
  BookOpen,
  Bot,
  MapPin,
  MessageSquare,
  Shield,
  Sparkles,
  Users,
} from "lucide-react";
import { Logo } from "@components/logo";
import { CanvasRevealCards } from "@components/landing";
import { BackgroundRippleEffect } from "@components/ui/background-ripple-effect";
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

const stats = [
  { value: "24/7", label: "Always available" },
  { value: "10+", label: "Campus tools" },
  { value: "AI", label: "Guided assistance" },
  { value: "1", label: "Unified workspace" },
];

const steps = [
  {
    step: "01",
    title: "Create your account",
    description: "Sign up with your email or Google in under a minute.",
    icon: Users,
  },
  {
    step: "02",
    title: "Ask anything",
    description: "Chat about courses, careers, campus services, or coding help.",
    icon: MessageSquare,
  },
  {
    step: "03",
    title: "Get things done",
    description: "Use agents, tools, and campus integrations from one dashboard.",
    icon: Sparkles,
  },
];

const capabilities = [
  "CGPA & course lookup",
  "Shuttle & fee info",
  "Career guidance",
  "Coding help",
  "Library research",
  "Voice & live agents",
];

export function LandingPage() {
  const { isAuthenticated, isLoading } = useAuth();
  const workspaceHref = isAuthenticated ? ROUTES.home : ROUTES.register;

  return (
    <div className="min-h-screen bg-background text-on-surface font-sans flex flex-col">
      <header className="sticky top-0 z-20 bg-surface-container-lowest/90 backdrop-blur-md border-b border-outline-variant/30">
        <div className={`${LANDING_WIDTH} h-16 sm:h-[4.25rem] flex items-center justify-between`}>
          <Logo size="md" />

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
        {/* Hero */}
        <section
          className={`relative ${LANDING_WIDTH} overflow-hidden pt-16 sm:pt-20 lg:pt-28 pb-20 lg:pb-28 text-center`}
        >
          <BackgroundRippleEffect />
          <div className="relative z-10 inline-flex items-center gap-2 rounded-full border border-outline-variant/50 bg-surface-container-lowest/80 px-4 py-1.5 text-sm text-on-surface-variant mb-8 backdrop-blur-sm">
            <Bot size={16} className="text-primary" />
            <span>Built for Daffodil International University</span>
          </div>
          <h1 className="relative z-10 text-4xl sm:text-5xl lg:text-6xl xl:text-6xl font-medium tracking-tight leading-[1.08] max-w-4xl mx-auto mb-6 lg:mb-8">
            Your guide to campus life
          </h1>
          <p className="relative z-10 text-base sm:text-lg lg:text-xl text-on-surface-variant max-w-2xl mx-auto leading-relaxed mb-10">
            Study support, career guidance, and campus services — all in one workspace.
          </p>
          <div className="relative z-10 flex flex-col sm:flex-row items-center justify-center gap-3 sm:gap-4">
            <Link
              to={workspaceHref}
              className="inline-flex items-center gap-2 px-6 py-3 text-sm font-medium bg-primary text-on-primary rounded-full hover:opacity-90 transition-opacity"
            >
              {isAuthenticated ? "Open workspace" : "Get started free"}
              <ArrowRight size={16} />
            </Link>
            <a
              href="#features"
              className="inline-flex items-center gap-2 px-6 py-3 text-sm font-medium text-on-surface-variant hover:text-on-surface rounded-full border border-outline-variant/50 transition-colors"
            >
              See what's included
            </a>
          </div>
        </section>

        {/* Stats */}
        <section className="border-y border-outline-variant/30 bg-surface-container-low/40">
          <div className={`${LANDING_WIDTH} py-10 sm:py-12`}>
            <div className="grid grid-cols-2 gap-6 sm:grid-cols-4 sm:gap-8">
              {stats.map(({ value, label }) => (
                <div key={label} className="text-center">
                  <p className="text-2xl sm:text-3xl font-semibold text-primary">{value}</p>
                  <p className="mt-1 text-sm text-on-surface-variant">{label}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Features */}
        <section id="features" className="bg-surface-container-low/50">
          <div className={`${LANDING_WIDTH} py-16 sm:py-20 lg:py-24`}>
            <div className="text-center max-w-2xl mx-auto mb-12 sm:mb-16">
              <h2 className="text-2xl sm:text-3xl lg:text-4xl font-medium mb-4">
                Everything you need on campus
              </h2>
              <p className="text-on-surface-variant">
                From academics to everyday campus tasks — one assistant, many capabilities.
              </p>
            </div>
            <div className="grid gap-6 sm:gap-8 lg:gap-10 sm:grid-cols-2 lg:grid-cols-3">
              {features.map(({ icon: Icon, title, description }) => (
                <div
                  key={title}
                  className="rounded-3xl bg-surface-container-lowest p-6 sm:p-8 text-left shadow-sm border border-outline-variant/20"
                >
                  <div className="w-11 h-11 sm:w-12 sm:h-12 rounded-2xl bg-primary/10 flex items-center justify-center mb-4 sm:mb-5">
                    <Icon size={22} className="text-primary" />
                  </div>
                  <h3 className="text-lg sm:text-xl font-medium mb-2">{title}</h3>
                  <p className="text-sm sm:text-base text-on-surface-variant leading-relaxed">{description}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Canvas reveal cards */}
        <section>
          <div className={`${LANDING_WIDTH} py-16 sm:py-20 lg:py-24`}>
            <div className="text-center max-w-2xl mx-auto mb-12 sm:mb-16">
              <h2 className="text-2xl sm:text-3xl lg:text-4xl font-medium mb-4">
                Hover to explore
              </h2>
              <p className="text-on-surface-variant">
                Interactive previews of what Daffodil Intelligence can help you with.
              </p>
            </div>
            <CanvasRevealCards />
          </div>
        </section>

        {/* How it works */}
        <section className="bg-surface-container-low/50">
          <div className={`${LANDING_WIDTH} py-16 sm:py-20 lg:py-24`}>
            <div className="text-center max-w-2xl mx-auto mb-12 sm:mb-16">
              <h2 className="text-2xl sm:text-3xl lg:text-4xl font-medium mb-4">
                How it works
              </h2>
              <p className="text-on-surface-variant">
                Get started in three simple steps.
              </p>
            </div>
            <div className="grid gap-8 sm:grid-cols-3">
              {steps.map(({ step, title, description, icon: Icon }) => (
                <div key={step} className="relative text-center sm:text-left">
                  <span className="text-5xl font-bold text-primary/15">{step}</span>
                  <div className="mt-4 mb-4 inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-primary/10">
                    <Icon size={22} className="text-primary" />
                  </div>
                  <h3 className="text-lg font-medium mb-2">{title}</h3>
                  <p className="text-sm text-on-surface-variant leading-relaxed">{description}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Capabilities */}
        <section>
          <div className={`${LANDING_WIDTH} py-16 sm:py-20 lg:py-24`}>
            <div className="rounded-3xl bg-surface-container-lowest border border-outline-variant/20 p-8 sm:p-12 lg:p-16 flex flex-col lg:flex-row items-center gap-10 lg:gap-16">
              <div className="flex-1 text-center lg:text-left">
                <h2 className="text-2xl sm:text-3xl font-medium mb-4">
                  Campus tools at your fingertips
                </h2>
                <p className="text-on-surface-variant mb-6 max-w-lg">
                  Ask about schedules, grades, fees, and more — or get help with assignments and career planning.
                </p>
                <Link
                  to={workspaceHref}
                  className="inline-flex items-center gap-2 text-sm font-medium text-primary hover:opacity-80 transition-opacity"
                >
                  Try it now
                  <ArrowRight size={16} />
                </Link>
              </div>
              <div className="flex flex-wrap justify-center gap-3 max-w-md lg:max-w-sm">
                {capabilities.map((item) => (
                  <span
                    key={item}
                    className="rounded-full border border-outline-variant/40 bg-surface-container-low px-4 py-2 text-sm text-on-surface-variant"
                  >
                    {item}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </section>

        {/* CTA */}
        <section className="bg-primary/5 border-t border-outline-variant/30">
          <div className={`${LANDING_WIDTH} py-16 sm:py-20 text-center`}>
            <h2 className="text-2xl sm:text-3xl lg:text-4xl font-medium mb-4 max-w-2xl mx-auto">
              Ready to simplify your campus life?
            </h2>
            <p className="text-on-surface-variant mb-8 max-w-xl mx-auto">
              Join Daffodil Intelligence and get a personal AI workspace built for DIU students.
            </p>
            <Link
              to={workspaceHref}
              className="inline-flex items-center gap-2 px-8 py-3.5 text-sm font-medium bg-primary text-on-primary rounded-full hover:opacity-90 transition-opacity"
            >
              {isAuthenticated ? "Go to workspace" : "Create free account"}
              <ArrowRight size={16} />
            </Link>
          </div>
        </section>
      </main>

      <footer className="py-10 lg:py-12 border-t border-outline-variant/30">
        <div className={`${LANDING_WIDTH}`}>
          <div className="flex flex-col sm:flex-row items-center justify-between gap-6">
            <Logo size="sm" />
            <nav className="flex flex-wrap items-center justify-center gap-4 sm:gap-6 text-sm text-on-surface-variant">
              <Link to={ROUTES.terms} className="hover:text-on-surface transition-colors">
                Terms
              </Link>
              <Link to={ROUTES.privacy} className="hover:text-on-surface transition-colors">
                Privacy
              </Link>
              <Link to={ROUTES.login} className="hover:text-on-surface transition-colors">
                Sign in
              </Link>
            </nav>
            <span className="text-sm text-on-surface-variant">
              © {new Date().getFullYear()} Daffodil Intelligence
            </span>
          </div>
        </div>
      </footer>
    </div>
  );
}
