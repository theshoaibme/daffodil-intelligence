import { BookOpen, MapPin, Shield } from "lucide-react";
import { BackgroundRippleEffect } from "@components/ui/background-ripple-effect";
import { PublicLayout } from "@layout";
import { PUBLIC_LAYOUT_WIDTH } from "@lib";

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
    <PublicLayout>
      <main className="flex-1 animate-fadeIn">
        <section
          className={`relative ${PUBLIC_LAYOUT_WIDTH} overflow-hidden pt-16 sm:pt-20 lg:pt-28 pb-20 lg:pb-28 text-center`}
        >
          <BackgroundRippleEffect />
          <h1 className="relative z-10 text-5xl sm:text-6xl lg:text-7xl font-semibold tracking-tight leading-[1.08] max-w-5xl mx-auto mb-6 lg:mb-8">
            Your guide to campus life
          </h1>
          <p className="relative z-10 text-lg sm:text-xl lg:text-2xl text-on-surface-variant max-w-3xl mx-auto leading-relaxed">
            Study support, career guidance, and campus services — all in one workspace.
          </p>
        </section>

        <section>
          <div className={`${PUBLIC_LAYOUT_WIDTH} py-16 sm:py-20 lg:py-24`}>
            <div className="grid gap-6 sm:gap-8 lg:gap-10 sm:grid-cols-2 lg:grid-cols-3">
              {features.map(({ icon: Icon, title, description }) => (
                <div
                  key={title}
                  className="rounded-3xl bg-surface-container-lowest p-6 sm:p-8 text-left shadow-sm"
                >
                  <div className="w-11 h-11 sm:w-12 sm:h-12 rounded-2xl bg-primary/10 flex items-center justify-center mb-4 sm:mb-5">
                    <Icon size={24} className="text-primary" />
                  </div>
                  <h2 className="text-xl sm:text-2xl font-semibold mb-3">{title}</h2>
                  <p className="text-base sm:text-lg text-on-surface-variant leading-relaxed">{description}</p>
                </div>
              ))}
            </div>
          </div>
        </section>
      </main>
    </PublicLayout>
  );
}
