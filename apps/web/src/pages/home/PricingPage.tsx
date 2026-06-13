import { Link } from "react-router-dom";
import { Check } from "lucide-react";
import { PublicLayout } from "@layout";
import { PUBLIC_LAYOUT_WIDTH, ROUTES } from "@lib";

const plans = [
  {
    name: "Student",
    price: "Free",
    description: "Core campus tools and AI guidance for enrolled students.",
    features: ["Class & campus agents", "Research library access", "Routine & reminders"],
    cta: "Get started",
    href: ROUTES.register,
    highlighted: false,
  },
  {
    name: "Campus",
    price: "Institutional",
    description: "Department-wide rollout with admin controls and integrations.",
    features: ["Everything in Student", "MCP connections", "Priority support"],
    cta: "Contact us",
    href: ROUTES.contacts,
    highlighted: true,
  },
];

export function PricingPage() {
  return (
    <PublicLayout>
      <main className={`${PUBLIC_LAYOUT_WIDTH} py-12 sm:py-16 flex-1 animate-fadeIn`}>
        <div className="max-w-3xl mx-auto text-center space-y-4 mb-12">
          <h1 className="text-3xl sm:text-4xl font-semibold tracking-tight text-on-surface">
            Pricing
          </h1>
          <p className="text-base text-on-surface-variant leading-relaxed">
            Simple plans for students and campus teams. No hidden fees for core student access.
          </p>
        </div>

        <div className="grid gap-6 md:grid-cols-2 max-w-4xl mx-auto">
          {plans.map((plan) => (
            <div
              key={plan.name}
              className={`rounded-3xl p-8 flex flex-col ${
                plan.highlighted
                  ? "bg-primary text-on-primary shadow-lg"
                  : "bg-surface-container-low text-on-surface"
              }`}
            >
              <h2 className="text-xl font-semibold">{plan.name}</h2>
              <p className={`mt-2 text-3xl font-semibold ${plan.highlighted ? "" : "text-primary"}`}>
                {plan.price}
              </p>
              <p
                className={`mt-3 text-sm leading-relaxed ${
                  plan.highlighted ? "text-on-primary/90" : "text-on-surface-variant"
                }`}
              >
                {plan.description}
              </p>
              <ul className="mt-6 space-y-2 flex-1">
                {plan.features.map((feature) => (
                  <li key={feature} className="flex items-center gap-2 text-sm">
                    <Check size={16} className="shrink-0" />
                    {feature}
                  </li>
                ))}
              </ul>
              <Link
                to={plan.href}
                className={`mt-8 inline-flex justify-center rounded-full px-5 py-2.5 text-sm font-semibold transition-opacity hover:opacity-90 ${
                  plan.highlighted
                    ? "bg-on-primary text-primary"
                    : "bg-primary text-on-primary"
                }`}
              >
                {plan.cta}
              </Link>
            </div>
          ))}
        </div>
      </main>
    </PublicLayout>
  );
}
