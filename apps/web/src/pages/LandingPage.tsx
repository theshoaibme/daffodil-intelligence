import { Link } from "react-router-dom";
import { Brain, GraduationCap, Bot, Shield, ArrowRight } from "lucide-react";
import { ROUTES } from "@lib";

const features = [
  {
    icon: Bot,
    title: "Multi-agent AI",
    description: "Academic, career, library, coding, and 20+ specialist agents orchestrated by one system.",
  },
  {
    icon: GraduationCap,
    title: "Built for DIU",
    description: "CGPA, courses, shuttle, fees, and campus services connected to university data.",
  },
  {
    icon: Shield,
    title: "Secure sign-in",
    description: "Email registration and Google OAuth. Your workspace stays private after login.",
  },
];

export function LandingPage() {
  return (
    <div className="min-h-screen bg-background text-on-surface font-sans flex flex-col">
      <header className="sticky top-0 z-20 border-b border-outline-variant/40 bg-surface-container-lowest/90 backdrop-blur-md">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
          <Link to={ROUTES.landing} className="flex items-center gap-2.5 font-semibold text-lg tracking-tight">
            <div className="w-9 h-9 rounded-xl bg-primary/10 flex items-center justify-center">
              <Brain size={20} className="text-primary" />
            </div>
            Daffodil Intelligence
          </Link>
          <nav className="flex items-center gap-2 sm:gap-3">
            <Link
              to={ROUTES.login}
              className="px-4 py-2 text-sm font-medium text-on-surface-variant hover:text-on-surface rounded-xl transition-colors"
            >
              Sign in
            </Link>
            <Link
              to={ROUTES.register}
              className="px-4 py-2.5 text-sm font-medium bg-primary text-on-primary rounded-full hover:opacity-90 transition-opacity"
            >
              Get started
            </Link>
          </nav>
        </div>
      </header>

      <main className="flex-1">
        <section className="max-w-6xl mx-auto px-4 sm:px-6 pt-16 sm:pt-24 pb-20 text-center">
          <p className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 text-primary text-xs font-medium mb-6">
            Daffodil International University
          </p>
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-medium tracking-tight leading-[1.1] max-w-3xl mx-auto mb-6">
            Your 360° AI operating system for campus life
          </h1>
          <p className="text-base sm:text-lg text-on-surface-variant max-w-2xl mx-auto mb-10 leading-relaxed">
            Plan, learn, automate, and get answers across academics, careers, wellness, and more —
            one intelligent workspace for students and staff.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
            <Link
              to={ROUTES.register}
              className="inline-flex items-center gap-2 px-6 py-3 rounded-full bg-primary text-on-primary text-sm font-semibold hover:opacity-90 transition-opacity"
            >
              Create free account
              <ArrowRight size={16} />
            </Link>
            <Link
              to={ROUTES.login}
              className="inline-flex items-center px-6 py-3 rounded-full border border-outline-variant text-sm font-semibold hover:bg-surface-container-high transition-colors"
            >
              Sign in
            </Link>
          </div>
        </section>

        <section className="border-t border-outline-variant/30 bg-surface-container-low/50">
          <div className="max-w-6xl mx-auto px-4 sm:px-6 py-16 sm:py-20">
            <div className="grid gap-6 sm:grid-cols-3">
              {features.map(({ icon: Icon, title, description }) => (
                <div
                  key={title}
                  className="rounded-3xl border border-outline-variant/50 bg-surface-container-lowest p-6 text-left"
                >
                  <div className="w-11 h-11 rounded-2xl bg-primary/10 flex items-center justify-center mb-4">
                    <Icon size={22} className="text-primary" />
                  </div>
                  <h2 className="text-lg font-medium mb-2">{title}</h2>
                  <p className="text-sm text-on-surface-variant leading-relaxed">{description}</p>
                </div>
              ))}
            </div>
          </div>
        </section>
      </main>

      <footer className="border-t border-outline-variant/30 py-8">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 flex flex-col sm:flex-row items-center justify-between gap-4 text-sm text-on-surface-variant">
          <span>© {new Date().getFullYear()} Daffodil Intelligence</span>
          <div className="flex gap-4">
            <Link to={ROUTES.login} className="hover:text-on-surface transition-colors">
              Sign in
            </Link>
            <Link to={ROUTES.register} className="hover:text-on-surface transition-colors">
              Register
            </Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
