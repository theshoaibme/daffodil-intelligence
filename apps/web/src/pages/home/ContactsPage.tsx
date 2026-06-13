import { Mail, MapPin, Phone } from "lucide-react";
import { PublicLayout } from "@layout";
import { PUBLIC_LAYOUT_WIDTH } from "@lib";

const contactItems = [
  {
    icon: Mail,
    title: "Email",
    detail: "info@diu.edu.bd",
    href: "mailto:info@diu.edu.bd",
  },
  {
    icon: Phone,
    title: "Support",
    detail: "it@diu.edu.bd",
    href: "mailto:it@diu.edu.bd",
  },
  {
    icon: MapPin,
    title: "Campus",
    detail: "Daffodil International University, Dhaka",
  },
];

export function ContactsPage() {
  return (
    <PublicLayout>
      <main className={`${PUBLIC_LAYOUT_WIDTH} py-12 sm:py-16 flex-1 animate-fadeIn`}>
        <div className="max-w-3xl mx-auto text-center space-y-4 mb-12">
          <h1 className="text-3xl sm:text-4xl font-semibold tracking-tight text-on-surface">
            Contact us
          </h1>
          <p className="text-base text-on-surface-variant leading-relaxed">
            Reach the Daffodil Intelligence team for support, partnerships, or campus inquiries.
          </p>
        </div>

        <div className="grid gap-5 sm:grid-cols-3 max-w-4xl mx-auto">
          {contactItems.map(({ icon: Icon, title, detail, href }) => (
            <div
              key={title}
              className="rounded-3xl bg-surface-container-low p-6 text-center space-y-3"
            >
              <div className="mx-auto w-11 h-11 rounded-2xl bg-primary/10 flex items-center justify-center text-primary">
                <Icon size={20} />
              </div>
              <h2 className="font-semibold text-on-surface">{title}</h2>
              {href ? (
                <a href={href} className="text-sm text-primary hover:underline">
                  {detail}
                </a>
              ) : (
                <p className="text-sm text-on-surface-variant">{detail}</p>
              )}
            </div>
          ))}
        </div>
      </main>
    </PublicLayout>
  );
}
