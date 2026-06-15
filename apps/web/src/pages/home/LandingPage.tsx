import { Link } from "react-router-dom";
import {
  ArrowRight,
  BookOpen,
  Bot,
  FileText,
  GraduationCap,
  Layers,
  MapPin,
  MessageSquare,
  Mic,
  Network,
  Shield,
  Sparkles,
  Users,
  Workflow,
} from "lucide-react";
import { CanvasRevealCards } from "@components/landing";
import { BackgroundRippleEffect } from "@components/ui/background-ripple-effect";
import { PublicLayout } from "@layout";
import { useAuth } from "@context";
import { PUBLIC_LAYOUT_WIDTH, ROUTES } from "@lib";

const highlights = [
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
  {
    icon: FileText,
    title: "Research library",
    description: "Browse 10,000+ papers with PDFs, filters, and full-text search.",
  },
  {
    icon: Network,
    title: "Academic network",
    description: "Connect with professors, universities, and research communities.",
  },
  {
    icon: Bot,
    title: "Multi-agent studio",
    description: "Run specialized agents for coding, campus ops, automation, and more.",
  },
];

const stats = [
  { value: "10k+", label: "Research papers" },
  { value: "24/7", label: "Always available" },
  { value: "11", label: "Research fields" },
  { value: "1", label: "Unified workspace" },
];

const platformModules = [
  {
    icon: FileText,
    title: "Research",
    description: "Search papers by category, open PDFs, and manage your own library in the studio.",
    href: ROUTES.publicResearchs,
    cta: "Browse papers",
  },
  {
    icon: Network,
    title: "Connections",
    description: "Intercommunication with top professors, universities, and academic institutions.",
    href: ROUTES.publicConnections,
    cta: "View network",
  },
  {
    icon: Layers,
    title: "Studio",
    description: "Your AI workspace — chat, agents, voice, computer use, and campus tools.",
    href: ROUTES.home,
    cta: "Open studio",
  },
];

const researchCategories = [
  "Machine Learning",
  "Natural Language Processing",
  "Computer Vision",
  "Cybersecurity",
  "Quantum Computing",
  "Bioinformatics",
  "Robotics",
  "Data Science",
  "Smart Grids",
  "AI & Education",
  "Computer Science",
];

const useCases = [
  {
    icon: GraduationCap,
    title: "Exam & assignment prep",
    description: "Summarize readings, explain concepts, and draft study notes from your materials.",
  },
  {
    icon: Workflow,
    title: "Project workflows",
    description: "Plan capstone work, break tasks into steps, and track progress with agents.",
  },
  {
    icon: Mic,
    title: "Voice & live sessions",
    description: "Talk through problems hands-free with live voice and real-time responses.",
  },
  {
    icon: MessageSquare,
    title: "Campus Q&A",
    description: "Ask about fees, shuttles, CGPA rules, and department info in plain language.",
  },
];

const integrations = [
  { label: "Google sign-in", detail: "Secure OAuth access" },
  { label: "Agent hub", detail: "Built-in & custom agents" },
  { label: "MCP tools", detail: "Extend with integrations" },
  { label: "PDF library", detail: "arXiv-backed papers" },
  { label: "Telegram", detail: "Chat on the go" },
  { label: "Live voice", detail: "Real-time audio" },
];

const faqs = [
  {
    q: "Is Daffodil Intelligence free for students?",
    a: "Yes — core campus tools, research browsing, and the student workspace are free to get started.",
  },
  {
    q: "Can I upload and manage my own research papers?",
    a: "Signed-in users can create, edit, and publish papers from the studio research library.",
  },
  {
    q: "What are Connections?",
    a: "An academic intercommunication layer to discover and message professors, universities, and research groups.",
  },
  {
    q: "Do papers include PDFs?",
    a: "The public library includes thousands of papers with direct PDF links, searchable by category and keyword.",
  },
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
  "Professor connections",
  "PDF paper library",
];

export function LandingPage() {
  const { isAuthenticated } = useAuth();
  const workspaceHref = isAuthenticated ? ROUTES.home : ROUTES.register;

  return (
    <PublicLayout>
      <main className="flex-1">
        {/* Hero */}
        <section
          className={`relative ${PUBLIC_LAYOUT_WIDTH} overflow-hidden pt-16 sm:pt-20 lg:pt-28 pb-20 lg:pb-28 text-center`}
        >
          <BackgroundRippleEffect />
          <h1 className="relative z-10 text-4xl sm:text-5xl lg:text-6xl font-medium tracking-tight leading-[1.08] max-w-4xl mx-auto mb-6 lg:mb-8">
            Your guide to campus life
          </h1>
          <p className="relative z-10 text-base sm:text-lg lg:text-xl text-on-surface-variant max-w-2xl mx-auto leading-relaxed mb-10">
            Study support, career guidance, research papers, and campus services — all in one workspace.
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
              className="inline-flex items-center gap-2 px-6 py-3 text-sm font-medium text-on-surface-variant hover:text-on-surface rounded-full transition-colors"
            >
              Explore features
            </a>
          </div>
        </section>

        {/* Stats */}
        <section className="bg-surface-container-low/40">
          <div className={`${PUBLIC_LAYOUT_WIDTH} py-10 sm:py-12`}>
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

        {/* Platform modules */}
        <section>
          <div className={`${PUBLIC_LAYOUT_WIDTH} py-16 sm:py-20 lg:py-24`}>
            <div className="text-center max-w-2xl mx-auto mb-12 sm:mb-16">
              <h2 className="text-2xl sm:text-3xl lg:text-4xl font-medium mb-4">
                Three pillars of the platform
              </h2>
              <p className="text-on-surface-variant">
                Research, academic connections, and a full AI studio — each built for university life.
              </p>
            </div>
            <div className="grid gap-6 lg:grid-cols-3 lg:gap-8">
              {platformModules.map(({ icon: Icon, title, description, href, cta }) => (
                <div key={title} className="bg-surface-container-lowest p-6 sm:p-8 flex flex-col">
                  <div className="w-12 h-12 bg-primary/10 flex items-center justify-center mb-5">
                    <Icon size={24} className="text-primary" />
                  </div>
                  <h3 className="text-xl font-medium mb-2">{title}</h3>
                  <p className="text-sm text-on-surface-variant leading-relaxed flex-1 mb-6">
                    {description}
                  </p>
                  <Link
                    to={href}
                    className="inline-flex items-center gap-2 text-sm font-medium text-primary hover:opacity-80 transition-opacity"
                  >
                    {cta}
                    <ArrowRight size={14} />
                  </Link>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Highlights */}
        <section className="bg-surface-container-low/50">
          <div className={`${PUBLIC_LAYOUT_WIDTH} py-16 sm:py-20 lg:py-24`}>
            <div className="text-center max-w-2xl mx-auto mb-12 sm:mb-16">
              <h2 className="text-2xl sm:text-3xl lg:text-4xl font-medium mb-4">
                Why students use it
              </h2>
              <p className="text-on-surface-variant">
                Everything from daily campus tasks to deep research — in one place.
              </p>
            </div>
            <div className="grid gap-6 sm:gap-8 sm:grid-cols-2 lg:grid-cols-3">
              {highlights.map(({ icon: Icon, title, description }) => (
                <div key={title} className="bg-surface-container-lowest p-6 sm:p-8 text-left">
                  <div className="w-11 h-11 sm:w-12 sm:h-12 bg-primary/10 flex items-center justify-center mb-4 sm:mb-5">
                    <Icon size={22} className="text-primary" />
                  </div>
                  <h2 className="text-lg sm:text-xl font-medium mb-2">{title}</h2>
                  <p className="text-sm sm:text-base text-on-surface-variant leading-relaxed">
                    {description}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Research spotlight */}
        <section>
          <div className={`${PUBLIC_LAYOUT_WIDTH} py-16 sm:py-20 lg:py-24`}>
            <div className="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-6 mb-10">
              <div className="max-w-xl">
                <h2 className="text-2xl sm:text-3xl lg:text-4xl font-medium mb-4">
                  Research library spotlight
                </h2>
                <p className="text-on-surface-variant leading-relaxed">
                  10,000+ real papers with PDFs across eleven fields. Filter by category or search
                  by title, author, and abstract.
                </p>
              </div>
              <Link
                to={ROUTES.publicResearchs}
                className="inline-flex items-center gap-2 px-6 py-3 text-sm font-medium bg-primary text-on-primary rounded-full hover:opacity-90 transition-opacity shrink-0 self-start lg:self-auto"
              >
                Open research library
                <ArrowRight size={16} />
              </Link>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
              {researchCategories.map((cat) => (
                <Link
                  key={cat}
                  to={`${ROUTES.publicResearchs}?category=${encodeURIComponent(cat)}`}
                  className="bg-surface-container-low px-4 py-3 text-sm text-on-surface-variant hover:bg-surface-container-high hover:text-on-surface transition-colors"
                >
                  {cat}
                </Link>
              ))}
            </div>
          </div>
        </section>

        {/* Canvas reveal features */}
        <section id="features" className="bg-surface-container-low/50">
          <div className={`${PUBLIC_LAYOUT_WIDTH} py-16 sm:py-20 lg:py-24`}>
            <div className="text-center max-w-2xl mx-auto mb-12 sm:mb-16">
              <h2 className="text-2xl sm:text-3xl lg:text-4xl font-medium mb-4">
                Hover to explore
              </h2>
              <p className="text-on-surface-variant">
                Interactive previews of what Daffodil Intelligence can help you with — research,
                connections, agents, and more.
              </p>
            </div>
            <CanvasRevealCards />
          </div>
        </section>

        {/* Use cases */}
        <section>
          <div className={`${PUBLIC_LAYOUT_WIDTH} py-16 sm:py-20 lg:py-24`}>
            <div className="text-center max-w-2xl mx-auto mb-12 sm:mb-16">
              <h2 className="text-2xl sm:text-3xl lg:text-4xl font-medium mb-4">
                Built for real student workflows
              </h2>
              <p className="text-on-surface-variant">
                From last-minute revision to long-form research — use the tools that fit your day.
              </p>
            </div>
            <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
              {useCases.map(({ icon: Icon, title, description }) => (
                <div key={title} className="bg-surface-container-lowest p-6">
                  <div className="w-10 h-10 bg-primary/10 flex items-center justify-center mb-4">
                    <Icon size={20} className="text-primary" />
                  </div>
                  <h3 className="text-base font-medium mb-2">{title}</h3>
                  <p className="text-sm text-on-surface-variant leading-relaxed">{description}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Integrations */}
        <section className="bg-surface-container-low/50">
          <div className={`${PUBLIC_LAYOUT_WIDTH} py-16 sm:py-20 lg:py-24`}>
            <div className="text-center max-w-2xl mx-auto mb-12">
              <h2 className="text-2xl sm:text-3xl font-medium mb-4">Connected & extensible</h2>
              <p className="text-on-surface-variant">
                Sign in securely, plug in tools, and scale from chat to full agent workflows.
              </p>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
              {integrations.map(({ label, detail }) => (
                <div key={label} className="bg-surface-container-lowest p-4 text-center">
                  <p className="text-sm font-medium text-on-surface">{label}</p>
                  <p className="mt-1 text-xs text-on-surface-variant">{detail}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* How it works */}
        <section>
          <div className={`${PUBLIC_LAYOUT_WIDTH} py-16 sm:py-20 lg:py-24`}>
            <div className="text-center max-w-2xl mx-auto mb-12 sm:mb-16">
              <h2 className="text-2xl sm:text-3xl lg:text-4xl font-medium mb-4">
                How it works
              </h2>
              <p className="text-on-surface-variant">Get started in three simple steps.</p>
            </div>
            <div className="grid gap-8 sm:grid-cols-3">
              {steps.map(({ step, title, description, icon: Icon }) => (
                <div key={step} className="relative text-center sm:text-left">
                  <span className="text-5xl font-bold text-primary/15">{step}</span>
                  <div className="mt-4 mb-4 inline-flex h-12 w-12 items-center justify-center bg-primary/10">
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
        <section className="bg-surface-container-low/50">
          <div className={`${PUBLIC_LAYOUT_WIDTH} py-16 sm:py-20 lg:py-24`}>
            <div className="bg-surface-container-lowest p-8 sm:p-12 lg:p-16 flex flex-col lg:flex-row items-center gap-10 lg:gap-16">
              <div className="flex-1 text-center lg:text-left">
                <h2 className="text-2xl sm:text-3xl font-medium mb-4">
                  Campus tools at your fingertips
                </h2>
                <p className="text-on-surface-variant mb-6 max-w-lg">
                  Ask about schedules, grades, fees, and more — browse 10,000+ research papers, connect
                  with academics, or get help with assignments and career planning.
                </p>
                <Link
                  to={ROUTES.publicResearchs}
                  className="inline-flex items-center gap-2 text-sm font-medium text-primary hover:opacity-80 transition-opacity mr-6"
                >
                  Browse research
                  <ArrowRight size={16} />
                </Link>
                <Link
                  to={ROUTES.publicConnections}
                  className="inline-flex items-center gap-2 text-sm font-medium text-primary hover:opacity-80 transition-opacity mr-6"
                >
                  View connections
                  <ArrowRight size={16} />
                </Link>
                <Link
                  to={workspaceHref}
                  className="inline-flex items-center gap-2 text-sm font-medium text-primary hover:opacity-80 transition-opacity"
                >
                  Try workspace
                  <ArrowRight size={16} />
                </Link>
              </div>
              <div className="flex flex-wrap justify-center gap-3 max-w-md lg:max-w-sm">
                {capabilities.map((item) => (
                  <span
                    key={item}
                    className="bg-surface-container-low px-4 py-2 text-sm text-on-surface-variant"
                  >
                    {item}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </section>

        {/* FAQ */}
        <section>
          <div className={`${PUBLIC_LAYOUT_WIDTH} py-16 sm:py-20 lg:py-24`}>
            <div className="text-center max-w-2xl mx-auto mb-12">
              <h2 className="text-2xl sm:text-3xl font-medium mb-4">Common questions</h2>
              <p className="text-on-surface-variant">
                Quick answers before you dive in. More details on{" "}
                <Link to={ROUTES.pricing} className="text-primary hover:opacity-80">
                  pricing
                </Link>{" "}
                and{" "}
                <Link to={ROUTES.contacts} className="text-primary hover:opacity-80">
                  contacts
                </Link>
                .
              </p>
            </div>
            <div className="max-w-3xl mx-auto divide-y divide-outline-variant/20">
              {faqs.map(({ q, a }) => (
                <div key={q} className="py-6 first:pt-0 last:pb-0">
                  <h3 className="text-base font-medium text-on-surface mb-2">{q}</h3>
                  <p className="text-sm text-on-surface-variant leading-relaxed">{a}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* CTA */}
        <section className="bg-primary/5">
          <div className={`${PUBLIC_LAYOUT_WIDTH} py-16 sm:py-20 text-center`}>
            <h2 className="text-2xl sm:text-3xl lg:text-4xl font-medium mb-4 max-w-2xl mx-auto">
              Ready to simplify your campus life?
            </h2>
            <p className="text-on-surface-variant mb-8 max-w-xl mx-auto">
              Join Daffodil Intelligence and get a personal AI workspace built for DIU students.
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
              <Link
                to={workspaceHref}
                className="inline-flex items-center gap-2 px-8 py-3.5 text-sm font-medium bg-primary text-on-primary rounded-full hover:opacity-90 transition-opacity"
              >
                {isAuthenticated ? "Go to workspace" : "Create free account"}
                <ArrowRight size={16} />
              </Link>
              <Link
                to={ROUTES.pricing}
                className="inline-flex items-center gap-2 px-8 py-3.5 text-sm font-medium text-on-surface-variant hover:text-on-surface rounded-full transition-colors"
              >
                View pricing
              </Link>
            </div>
          </div>
        </section>
      </main>
    </PublicLayout>
  );
}
