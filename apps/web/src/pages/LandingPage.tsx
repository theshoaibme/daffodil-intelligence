import { useState, useRef } from "react";
import { Link } from "react-router-dom";
import {
  ArrowRight,
  Bot,
  GraduationCap,
  Shield,
  Cpu,
  Mic,
  Compass,
  Layers,
  Zap,
  Globe,
  Code2,
  BrainCircuit,
  Wrench,
  MessageSquare,
  Monitor,
  ChevronDown,
  Menu,
  X,
  Check,
  Sparkles,
  Network,
  Workflow,
  Mail,
  MapPin,
  Phone,
} from "lucide-react";
import { ROUTES } from "@lib";

/* ─── Product Items (hover dropdown) ─── */
const productItems = [
  { icon: Bot, label: "Agent Hub", desc: "20+ specialist AI agents", to: ROUTES.agentHub },
  { icon: Wrench, label: "Skills Hub", desc: "Custom skill builder", to: ROUTES.skills },
  { icon: Compass, label: "Guidance Desk", desc: "Academic advisor AI", to: ROUTES.guidance },
  { icon: Cpu, label: "Model Hub", desc: "Multi-model orchestrator", to: ROUTES.model },
  { icon: Mic, label: "Live Voice", desc: "Real-time voice AI", to: ROUTES.live },
  { icon: Monitor, label: "Computer Use", desc: "Desktop automation", to: ROUTES.computer },
];

/* ─── Feature Items (hover dropdown) ─── */
const featureItems = [
  { icon: Network, label: "MCP Builders", desc: "Model Context Protocol tools" },
  { icon: BrainCircuit, label: "Multi-Agent System", desc: "Orchestrated agent pipelines" },
  { icon: Workflow, label: "RAG Pipeline", desc: "Semantic memory & retrieval" },
  { icon: Code2, label: "Code Generation", desc: "AI-powered coding assistant" },
  { icon: Globe, label: "Web Automation", desc: "Browser & scraping agents" },
  { icon: MessageSquare, label: "Telegram Bot", desc: "Cross-platform messaging" },
];

/* ─── Features Grid (main section) ─── */
const features = [
  {
    icon: Bot,
    title: "Multi-Agent AI",
    description:
      "Academic, career, library, coding, and 20+ specialist agents orchestrated by one intelligent system.",
  },
  {
    icon: GraduationCap,
    title: "Built for DIU",
    description:
      "CGPA calculator, course tracker, shuttle directory, fees manager, and campus services connected to university data.",
  },
  {
    icon: Shield,
    title: "Secure Authentication",
    description:
      "Email registration, Google OAuth, and JWT-based sessions. Your workspace stays private and encrypted.",
  },
  {
    icon: Network,
    title: "MCP Protocol",
    description:
      "Model Context Protocol integration for building custom AI tools, connectors, and agent pipelines.",
  },
  {
    icon: Mic,
    title: "Live Voice AI",
    description:
      "Real-time voice conversations with AI agents using edge text-to-speech and streaming responses.",
  },
  {
    icon: Monitor,
    title: "Computer Use",
    description:
      "Desktop automation with screen capture, mouse/keyboard control, and AI-guided task execution.",
  },
  {
    icon: Workflow,
    title: "RAG Pipeline",
    description:
      "Retrieval-Augmented Generation with Qdrant vector store, semantic memory, and document embeddings.",
  },
  {
    icon: Code2,
    title: "Code Generation",
    description:
      "AI-powered coding assistant with multi-language support, code review, and debugging capabilities.",
  },
  {
    icon: MessageSquare,
    title: "Telegram Integration",
    description:
      "Cross-platform messaging bot for campus notifications, task updates, and AI assistant access.",
  },
];

/* ─── Pricing ─── */
const pricingPlans = [
  {
    name: "Free",
    price: "0",
    desc: "For students getting started",
    features: ["5 AI agent queries/day", "CGPA calculator", "Shuttle tracker", "Basic campus info"],
    cta: "Get Started",
    popular: false,
  },
  {
    name: "Pro",
    price: "9",
    desc: "For power users & researchers",
    features: [
      "Unlimited AI queries",
      "All 20+ agents",
      "MCP Builder access",
      "Live Voice AI",
      "RAG pipeline",
      "Priority support",
    ],
    cta: "Start Free Trial",
    popular: true,
  },
  {
    name: "Enterprise",
    price: "Custom",
    desc: "For departments & institutions",
    features: [
      "Everything in Pro",
      "Custom agent training",
      "SSO & LDAP auth",
      "Dedicated infrastructure",
      "SLA guarantee",
      "On-premise deployment",
    ],
    cta: "Contact Sales",
    popular: false,
  },
];

/* ─── Hover Dropdown Component ─── */
function NavDropdown({
  label,
  items,
  hasLinks,
}: {
  label: string;
  items: { icon: React.ElementType; label: string; desc: string; to?: string }[];
  hasLinks?: boolean;
}) {
  const [open, setOpen] = useState(false);
  const timeout = useRef<ReturnType<typeof setTimeout> | null>(null);

  const enter = () => {
    if (timeout.current) clearTimeout(timeout.current);
    setOpen(true);
  };
  const leave = () => {
    timeout.current = setTimeout(() => setOpen(false), 200);
  };

  return (
    <div className="relative" onMouseEnter={enter} onMouseLeave={leave}>
      <button className="flex items-center gap-1 hover:text-black transition-colors cursor-pointer">
        {label}
        <ChevronDown
          size={12}
          className={`transition-transform duration-200 ${open ? "rotate-180" : ""}`}
        />
      </button>
      {open && (
        <div className="absolute top-full left-1/2 -translate-x-1/2 pt-3 z-50">
          <div className="backdrop-blur-[40px] bg-white/80 border border-black/10 rounded-2xl shadow-xl p-3 min-w-[280px] grid gap-0.5">
            {items.map((item) => {
              const Inner = (
                <div className="flex items-start gap-3 p-2.5 rounded-xl hover:bg-[#f4f2ff] transition-colors cursor-pointer group">
                  <div className="w-9 h-9 rounded-xl bg-[#4259ff]/10 flex items-center justify-center shrink-0 group-hover:bg-[#4259ff]/20 transition-colors">
                    <item.icon size={18} className="text-[#4259ff]" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-black">{item.label}</p>
                    <p className="text-xs text-[#444656]/70">{item.desc}</p>
                  </div>
                </div>
              );
              return hasLinks && item.to ? (
                <Link key={item.label} to={item.to}>
                  {Inner}
                </Link>
              ) : (
                <div key={item.label}>{Inner}</div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

/* ─── Main Landing Page ─── */
export function LandingPage() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  /* Water ripple effect */
  const handleWaterRipple = (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    const rippleContainer = document.createElement("div");
    rippleContainer.className = "absolute pointer-events-none z-50 overflow-visible";
    rippleContainer.style.left = `${x}px`;
    rippleContainer.style.top = `${y}px`;
    e.currentTarget.appendChild(rippleContainer);

    const waves = 3;
    for (let i = 0; i < waves; i++) {
      const wave = document.createElement("div");
      wave.className =
        "absolute rounded-full border border-[#4259ff]/30 bg-[#4259ff]/5 -translate-x-1/2 -translate-y-1/2 opacity-70 transition-all duration-300 ease-out";
      wave.style.width = "0px";
      wave.style.height = "0px";

      setTimeout(() => {
        rippleContainer.appendChild(wave);
        requestAnimationFrame(() => {
          wave.style.width = `${120 + i * 40}px`;
          wave.style.height = `${120 + i * 40}px`;
          wave.style.opacity = "0";
        });
      }, i * 50);
    }

    setTimeout(() => {
      rippleContainer.remove();
    }, waves * 50 + 300);
  };

  const scrollTo = (id: string) => {
    document.getElementById(id)?.scrollIntoView({ behavior: "smooth" });
    setMobileMenuOpen(false);
  };

  return (
    <div
      onMouseDown={handleWaterRipple}
      className="min-h-screen bg-white text-[#1a1b24] font-sans flex flex-col relative overflow-hidden antialiased cursor-default select-none"
    >
      {/* ─── Background Gradient Glows ─── */}
      <div className="absolute top-0 left-0 w-[600px] h-[600px] rounded-full bg-[#60B1FF] opacity-35 blur-[120px] -translate-x-1/3 -translate-y-1/3 pointer-events-none z-0" />
      <div className="absolute top-[50px] left-[100px] w-[500px] h-[500px] rounded-full bg-[#319AFF] opacity-30 blur-[110px] -translate-x-1/4 -translate-y-1/4 pointer-events-none z-0" />
      <div className="absolute bottom-0 right-0 w-[400px] h-[400px] rounded-full bg-[#4259ff] opacity-15 blur-[100px] translate-x-1/4 translate-y-1/4 pointer-events-none z-0" />

      {/* ═══════════════ NAVBAR ═══════════════ */}
      <header className="sticky top-[30px] z-50 mx-auto w-fit px-4 pointer-events-auto">
        <div className="backdrop-blur-[50px] bg-white/30 rounded-full border border-black/10 shadow-[inset_0_4px_4px_rgba(255,255,255,0.25)] flex items-center justify-between gap-10 py-3 px-6 max-w-full">
          <Link
            to={ROUTES.landing}
            className="font-fustat font-bold text-xl tracking-tight text-black flex items-center gap-2 shrink-0"
          >
            Daffodil Intelligence
          </Link>

          {/* Desktop Nav */}
          <nav className="hidden lg:flex items-center gap-6 font-inter font-medium text-xs text-[#444656]">
            <button onClick={() => scrollTo("hero")} className="hover:text-black transition-colors cursor-pointer">
              Home
            </button>
            <NavDropdown label="Products" items={productItems} hasLinks />
            <NavDropdown label="Features" items={featureItems} />
            <button onClick={() => scrollTo("pricing")} className="hover:text-black transition-colors cursor-pointer">
              Pricing
            </button>
            <button onClick={() => scrollTo("contact")} className="hover:text-black transition-colors cursor-pointer">
              Contact
            </button>
          </nav>

          {/* Desktop CTA */}
          <Link
            to={ROUTES.register}
            className="hidden lg:flex backdrop-blur-[10px] bg-white/20 border border-black/10 rounded-full px-5 py-2 font-inter font-medium text-sm items-center gap-1.5 hover:bg-white/40 transition-all text-black hover:scale-[1.02] active:scale-[0.98] cursor-pointer shadow-sm shrink-0"
          >
            SignUp
            <ArrowRight size={14} />
          </Link>

          {/* Mobile Hamburger */}
          <button
            className="lg:hidden text-black p-1"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          >
            {mobileMenuOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>

        {/* Mobile Menu */}
        {mobileMenuOpen && (
          <div className="lg:hidden mt-2 backdrop-blur-[40px] bg-white/90 border border-black/10 rounded-2xl shadow-xl p-4 font-inter text-sm text-[#444656] flex flex-col gap-3">
            <button onClick={() => scrollTo("hero")} className="text-left hover:text-black transition-colors">Home</button>
            <button onClick={() => scrollTo("features")} className="text-left hover:text-black transition-colors">Features</button>
            <button onClick={() => scrollTo("pricing")} className="text-left hover:text-black transition-colors">Pricing</button>
            <button onClick={() => scrollTo("contact")} className="text-left hover:text-black transition-colors">Contact</button>
            <hr className="border-black/10" />
            <p className="text-xs font-medium text-black/50 uppercase tracking-wider">Products</p>
            {productItems.map((p) => (
              <Link key={p.label} to={p.to} className="flex items-center gap-2 hover:text-black transition-colors pl-2">
                <p.icon size={14} className="text-[#4259ff]" />
                {p.label}
              </Link>
            ))}
            <hr className="border-black/10" />
            <Link
              to={ROUTES.register}
              className="bg-[#4259ff] text-white rounded-full py-2.5 text-center font-medium hover:bg-[#3348d6] transition-colors"
            >
              Sign Up Free
            </Link>
          </div>
        )}
      </header>

      {/* ═══════════════ HERO ═══════════════ */}
      <main id="hero" className="flex-1 relative z-10 w-full max-w-[1600px] mx-auto px-6 lg:px-16 pt-16 sm:pt-24 pb-20">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 lg:gap-8 items-center">
          {/* Hero Content (Left) */}
          <section className="flex flex-col items-start text-left">
            {/* Social Proof Badge */}
            <div className="inline-flex items-center gap-2 bg-[#f4f2ff] px-3.5 py-1.5 rounded-full border border-[#c5c5d9]/30 mb-6 shadow-sm">
              <span className="text-xs font-inter font-medium text-[#444656]">
                Rated 4.9/5 by 2700+ campus users
              </span>
              <div className="flex items-center gap-0.5">
                {[...Array(5)].map((_, i) => (
                  <svg key={i} className="w-3.5 h-3.5 fill-[#FF801E] stroke-[#FF801E]" viewBox="0 0 24 24">
                    <path d="M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z" />
                  </svg>
                ))}
              </div>
            </div>

            {/* Headline */}
            <h1 className="text-5xl sm:text-7xl lg:text-[75px] leading-[1.05] tracking-[-2px] font-fustat font-bold text-black mb-6 antialiased">
              Work smarter,<br />achieve faster
            </h1>

            {/* Subheadline */}
            <p className="text-base sm:text-[18px] font-inter text-[#444656] tracking-[-0.5px] leading-relaxed mb-8 max-w-xl antialiased">
              Your all-in-one campus AI assistant. Calculate CGPA, orchestrate 20+ specialist agents, build custom MCP tools, and automate university workflows — all in one premium workspace.
            </p>

            {/* CTAs */}
            <div className="flex flex-col sm:flex-row gap-3 w-full sm:w-auto">
              <Link
                to={ROUTES.register}
                className="inline-flex items-center gap-3 px-6 py-4 rounded-full bg-[#4259ff] shadow-[inset_0_4px_4px_rgba(255,255,255,0.25)] text-white font-inter font-semibold text-sm hover:scale-[1.02] active:scale-[0.98] transition-all duration-300 justify-center cursor-pointer"
              >
                Get Started Free
                <div className="w-5 h-5 rounded-full bg-white flex items-center justify-center text-[#4259ff]">
                  <ArrowRight size={12} className="stroke-[3]" />
                </div>
              </Link>
              <button
                onClick={() => scrollTo("features")}
                className="inline-flex items-center gap-2 px-6 py-4 rounded-full border border-black/10 bg-white/50 backdrop-blur-sm text-black font-inter font-medium text-sm hover:bg-white/80 transition-all duration-300 justify-center cursor-pointer"
              >
                Explore Features
              </button>
            </div>
          </section>

          {/* Glassy Orb (Right) */}
          <section className="relative w-full h-[350px] sm:h-[450px] lg:h-[550px] flex items-center justify-center lg:justify-end overflow-visible">
            <div className="w-[125%] h-[125%] max-w-[600px] max-h-[600px] relative scale-125 pointer-events-none mix-blend-screen flex items-center justify-center">
              <video
                autoPlay
                loop
                muted
                playsInline
                className="w-full h-full object-cover"
                style={{ filter: "hue-rotate(-55deg) saturate(250%) brightness(1.2) contrast(1.1)" }}
              >
                <source src="https://future.co/images/homepage/glassy-orb/orb-purple.webm" type="video/webm" />
              </video>
            </div>
          </section>
        </div>


      </main>

      {/* ═══════════════ FEATURES SECTION ═══════════════ */}
      <section id="features" className="relative z-20 py-20 sm:py-28">
        {/* Subtle BG accent */}
        <div className="absolute inset-0 bg-gradient-to-b from-white via-[#f4f2ff]/40 to-white pointer-events-none" />
        <div className="relative max-w-6xl mx-auto px-4 sm:px-6">
          {/* Section Header */}
          <div className="text-center mb-16">
            <div className="inline-flex items-center gap-2 bg-[#4259ff]/10 px-3.5 py-1.5 rounded-full mb-4">
              <Sparkles size={14} className="text-[#4259ff]" />
              <span className="text-xs font-inter font-medium text-[#4259ff]">
                Platform Features
              </span>
            </div>
            <h2 className="text-3xl sm:text-4xl lg:text-5xl font-fustat font-bold tracking-[-1px] mb-4">
              Everything you need,<br />one intelligent workspace
            </h2>
            <p className="text-base font-inter text-[#444656] max-w-2xl mx-auto">
              From multi-agent AI to MCP builders, Daffodil Intelligence gives you the most powerful campus AI platform available.
            </p>
          </div>

          {/* Features Grid */}
          <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {features.map(({ icon: Icon, title, description }) => (
              <div
                key={title}
                className="rounded-3xl border border-[#c5c5d9]/30 bg-white/80 backdrop-blur-sm p-6 text-left shadow-sm hover:shadow-md hover:border-[#4259ff]/30 hover:-translate-y-1 transition-all duration-300 group"
              >
                <div className="w-11 h-11 rounded-2xl bg-[#4259ff]/10 flex items-center justify-center mb-4 group-hover:bg-[#4259ff]/20 transition-colors">
                  <Icon size={22} className="text-[#4259ff]" />
                </div>
                <h3 className="text-lg font-medium mb-2">{title}</h3>
                <p className="text-sm text-[#444656] leading-relaxed">{description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ═══════════════ MCP BUILDERS HIGHLIGHT ═══════════════ */}
      <section className="relative z-20 py-20 sm:py-28 overflow-hidden">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] rounded-full bg-[#4259ff] opacity-5 blur-[120px] pointer-events-none" />
        <div className="relative max-w-6xl mx-auto px-4 sm:px-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 lg:gap-16 items-center">
            {/* Left — Content */}
            <div>
              <div className="inline-flex items-center gap-2 bg-[#4259ff]/10 px-3.5 py-1.5 rounded-full mb-6">
                <Network size={14} className="text-[#4259ff]" />
                <span className="text-xs font-inter font-medium text-[#4259ff]">MCP Builders</span>
              </div>
              <h2 className="text-3xl sm:text-4xl font-fustat font-bold tracking-[-1px] mb-5">
                Build custom AI tools with<br />Model Context Protocol
              </h2>
              <p className="text-base font-inter text-[#444656] leading-relaxed mb-8 max-w-lg">
                Create, connect, and deploy custom AI tool servers using the open MCP standard. Build connectors to university APIs, external services, and data sources — then wire them into your agent pipelines.
              </p>
              <ul className="space-y-3 mb-8">
                {[
                  "Stdio & HTTP transport modes",
                  "Connect Google Genai, OpenAI, and custom models",
                  "Plug into campus SIS, library, HR, and transport APIs",
                  "Visual tool builder with live testing",
                  "Deploy as standalone MCP servers",
                ].map((item) => (
                  <li key={item} className="flex items-start gap-2.5 text-sm font-inter text-[#1a1b24]">
                    <Check size={16} className="text-[#4259ff] mt-0.5 shrink-0" />
                    {item}
                  </li>
                ))}
              </ul>
              <Link
                to={ROUTES.register}
                className="inline-flex items-center gap-2 px-5 py-3 rounded-full bg-[#4259ff] text-white font-inter font-medium text-sm hover:scale-[1.02] active:scale-[0.98] transition-all cursor-pointer"
              >
                Start Building
                <ArrowRight size={14} />
              </Link>
            </div>

            {/* Right — Visual Card Grid */}
            <div className="grid grid-cols-2 gap-4">
              {[
                { icon: Layers, label: "Tool Registry", desc: "Register & manage AI tools" },
                { icon: Zap, label: "Live Testing", desc: "Test tools in real-time" },
                { icon: Globe, label: "API Connectors", desc: "Connect any REST/GraphQL API" },
                { icon: BrainCircuit, label: "Agent Wiring", desc: "Wire tools to agent flows" },
              ].map(({ icon: Icon, label, desc }) => (
                <div
                  key={label}
                  className="rounded-2xl border border-[#c5c5d9]/30 bg-white/60 backdrop-blur-sm p-5 hover:border-[#4259ff]/30 hover:shadow-md transition-all duration-300 group"
                >
                  <div className="w-10 h-10 rounded-xl bg-[#4259ff]/10 flex items-center justify-center mb-3 group-hover:bg-[#4259ff]/20 transition-colors">
                    <Icon size={20} className="text-[#4259ff]" />
                  </div>
                  <p className="text-sm font-medium mb-1">{label}</p>
                  <p className="text-xs text-[#444656]/70">{desc}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ═══════════════ PRICING ═══════════════ */}
      <section id="pricing" className="relative z-20 py-20 sm:py-28">
        <div className="absolute inset-0 bg-gradient-to-b from-white via-[#f4f2ff]/30 to-white pointer-events-none" />
        <div className="relative max-w-5xl mx-auto px-4 sm:px-6">
          <div className="text-center mb-16">
            <div className="inline-flex items-center gap-2 bg-[#4259ff]/10 px-3.5 py-1.5 rounded-full mb-4">
              <Sparkles size={14} className="text-[#4259ff]" />
              <span className="text-xs font-inter font-medium text-[#4259ff]">Pricing</span>
            </div>
            <h2 className="text-3xl sm:text-4xl lg:text-5xl font-fustat font-bold tracking-[-1px] mb-4">
              Simple, transparent pricing
            </h2>
            <p className="text-base font-inter text-[#444656] max-w-xl mx-auto">
              Start free and scale as you grow. No hidden fees.
            </p>
          </div>

          <div className="grid gap-6 sm:grid-cols-3">
            {pricingPlans.map((plan) => (
              <div
                key={plan.name}
                className={`rounded-3xl border p-6 sm:p-8 flex flex-col transition-all duration-300 hover:-translate-y-1 ${
                  plan.popular
                    ? "border-[#4259ff]/40 bg-white shadow-xl shadow-[#4259ff]/10 relative"
                    : "border-[#c5c5d9]/30 bg-white/80 backdrop-blur-sm shadow-sm hover:shadow-md"
                }`}
              >
                {plan.popular && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-[#4259ff] text-white text-xs font-inter font-medium px-3 py-1 rounded-full">
                    Most Popular
                  </div>
                )}
                <h3 className="text-lg font-medium mb-1">{plan.name}</h3>
                <p className="text-sm text-[#444656] mb-4">{plan.desc}</p>
                <div className="flex items-baseline gap-1 mb-6">
                  {plan.price === "Custom" ? (
                    <span className="text-3xl font-fustat font-bold">Custom</span>
                  ) : (
                    <>
                      <span className="text-3xl font-fustat font-bold">${plan.price}</span>
                      <span className="text-sm text-[#444656]">/mo</span>
                    </>
                  )}
                </div>
                <ul className="space-y-2.5 mb-8 flex-1">
                  {plan.features.map((f) => (
                    <li key={f} className="flex items-start gap-2 text-sm font-inter text-[#1a1b24]">
                      <Check size={15} className="text-[#4259ff] mt-0.5 shrink-0" />
                      {f}
                    </li>
                  ))}
                </ul>
                <Link
                  to={ROUTES.register}
                  className={`text-center py-3 rounded-full font-inter font-medium text-sm transition-all hover:scale-[1.02] active:scale-[0.98] cursor-pointer ${
                    plan.popular
                      ? "bg-[#4259ff] text-white"
                      : "bg-white border border-black/10 text-black hover:bg-[#f4f2ff]"
                  }`}
                >
                  {plan.cta}
                </Link>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ═══════════════ CONTACT ═══════════════ */}
      <section id="contact" className="relative z-20 py-20 sm:py-28">
        <div className="max-w-5xl mx-auto px-4 sm:px-6">
          <div className="text-center mb-16">
            <div className="inline-flex items-center gap-2 bg-[#4259ff]/10 px-3.5 py-1.5 rounded-full mb-4">
              <Mail size={14} className="text-[#4259ff]" />
              <span className="text-xs font-inter font-medium text-[#4259ff]">Get in Touch</span>
            </div>
            <h2 className="text-3xl sm:text-4xl lg:text-5xl font-fustat font-bold tracking-[-1px] mb-4">
              Contact us
            </h2>
            <p className="text-base font-inter text-[#444656] max-w-xl mx-auto">
              Have questions? We'd love to hear from you.
            </p>
          </div>

          <div className="grid gap-6 sm:grid-cols-3 max-w-3xl mx-auto">
            {[
              {
                icon: Mail,
                title: "Email",
                info: "support@daffodil.edu.bd",
                link: "mailto:support@daffodil.edu.bd",
              },
              {
                icon: Phone,
                title: "Phone",
                info: "+880 2-7744 1269",
                link: "tel:+88027744126",
              },
              {
                icon: MapPin,
                title: "Address",
                info: "Daffodil International University, Ashulia, Dhaka",
                link: "https://maps.google.com/?q=Daffodil+International+University",
              },
            ].map(({ icon: Icon, title, info, link }) => (
              <a
                key={title}
                href={link}
                target="_blank"
                rel="noopener noreferrer"
                className="rounded-3xl border border-[#c5c5d9]/30 bg-white/80 backdrop-blur-sm p-6 text-center hover:shadow-md hover:border-[#4259ff]/30 hover:-translate-y-1 transition-all duration-300 group"
              >
                <div className="w-11 h-11 rounded-2xl bg-[#4259ff]/10 flex items-center justify-center mb-4 mx-auto group-hover:bg-[#4259ff]/20 transition-colors">
                  <Icon size={22} className="text-[#4259ff]" />
                </div>
                <h3 className="text-sm font-medium mb-1">{title}</h3>
                <p className="text-xs text-[#444656]">{info}</p>
              </a>
            ))}
          </div>
        </div>
      </section>

      {/* ═══════════════ FOOTER ═══════════════ */}
      <footer className="border-t border-[#c5c5d9]/20 py-10 relative z-20 bg-white">
        <div className="max-w-6xl mx-auto px-4 sm:px-6">
          <div className="grid gap-8 sm:grid-cols-4 mb-10">
            {/* Brand */}
            <div className="sm:col-span-1">
              <h4 className="font-fustat font-bold text-lg mb-3">Daffodil Intelligence</h4>
              <p className="text-xs text-[#444656] leading-relaxed">
                The premium campus AI platform built for Daffodil International University.
              </p>
            </div>
            {/* Products */}
            <div>
              <h5 className="text-xs font-inter font-medium text-black/50 uppercase tracking-wider mb-3">Products</h5>
              <ul className="space-y-2">
                {productItems.map((p) => (
                  <li key={p.label}>
                    <Link to={p.to} className="text-sm text-[#444656] hover:text-black transition-colors">
                      {p.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
            {/* Resources */}
            <div>
              <h5 className="text-xs font-inter font-medium text-black/50 uppercase tracking-wider mb-3">Resources</h5>
              <ul className="space-y-2">
                {["MCP Builders", "Documentation", "API Reference", "Changelog"].map((r) => (
                  <li key={r}>
                    <span className="text-sm text-[#444656] hover:text-black transition-colors cursor-pointer">{r}</span>
                  </li>
                ))}
              </ul>
            </div>
            {/* Legal */}
            <div>
              <h5 className="text-xs font-inter font-medium text-black/50 uppercase tracking-wider mb-3">Legal</h5>
              <ul className="space-y-2">
                <li><Link to={ROUTES.terms} className="text-sm text-[#444656] hover:text-black transition-colors">Terms of Service</Link></li>
                <li><Link to={ROUTES.privacy} className="text-sm text-[#444656] hover:text-black transition-colors">Privacy Policy</Link></li>
                <li><Link to={ROUTES.login} className="text-sm text-[#444656] hover:text-black transition-colors">Sign in</Link></li>
                <li><Link to={ROUTES.register} className="text-sm text-[#444656] hover:text-black transition-colors">Register</Link></li>
              </ul>
            </div>
          </div>
          <div className="border-t border-[#c5c5d9]/20 pt-6 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-[#444656]">
            <span>© {new Date().getFullYear()} Daffodil Intelligence. All rights reserved.</span>
            <span>Built with ❤️ for DIU Campus</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
