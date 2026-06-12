import { Link } from "react-router-dom";
import { GraduationCap, BookOpen, MapPin, Shield, ArrowRight } from "lucide-react";
import { ROUTES } from "@lib";

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
  return (
    <div className="min-h-screen bg-background text-on-surface font-sans flex flex-col">
      <header className="sticky top-0 z-20 bg-surface-container-lowest/90 backdrop-blur-md">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
          <Link to={ROUTES.landing} className="flex items-center gap-2.5 tracking-tight">
            <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center shrink-0">
              <GraduationCap size={22} className="text-primary" />
            </div>
            <span className="text-2xl sm:text-3xl font-bold leading-none">
              <span className="text-primary">Daffodil</span>
              <span className="text-on-surface"> Intelligence</span>
            </span>
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
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-medium tracking-tight leading-[1.1] max-w-3xl mx-auto mb-6">
            Your guide to campus life
          </h1>
          <p className="text-base sm:text-lg text-on-surface-variant max-w-xl mx-auto mb-10 leading-relaxed">
            Study support, career guidance, and campus services — all in one workspace.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
            <Link
              to={ROUTES.register}
              className="inline-flex items-center gap-2 px-6 py-3 rounded-full bg-primary text-on-primary text-sm font-semibold hover:opacity-90 transition-opacity"
            >
              Get started
              <ArrowRight size={16} />
            </Link>
            <Link
              to={ROUTES.login}
              className="inline-flex items-center px-6 py-3 rounded-full bg-surface-container-high/80 text-sm font-semibold hover:bg-surface-container-high transition-colors"
            >
              Sign in
            </Link>
          </div>
        </section>

        <section className="bg-surface-container-low/50">
          <div className="max-w-6xl mx-auto px-4 sm:px-6 py-16 sm:py-20">
            <div className="grid gap-6 sm:grid-cols-3">
              {features.map(({ icon: Icon, title, description }) => (
                <div
                  key={title}
                  className="rounded-3xl bg-surface-container-lowest p-6 text-left shadow-sm"
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

      <footer className="py-8">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 text-center text-sm text-on-surface-variant">
          <span>© {new Date().getFullYear()} Daffodil Intelligence</span>
        </div>
      </footer>
    </div>
  );
}
