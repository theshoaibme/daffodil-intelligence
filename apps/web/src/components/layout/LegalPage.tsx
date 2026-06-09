import { Link } from "react-router-dom";
import { ROUTES } from "@lib";

interface LegalPageProps {
  title: string;
  children: React.ReactNode;
}

function LegalPage({ title, children }: LegalPageProps) {
  return (
    <div className="min-h-screen bg-background text-on-surface font-sans px-4 py-10 sm:px-6">
      <div className="max-w-2xl mx-auto">
        <Link to={ROUTES.landing} className="text-sm text-primary hover:underline">
          ← Daffodil Intelligence
        </Link>
        <h1 className="text-3xl font-medium mt-6 mb-4">{title}</h1>
        <div className="prose prose-sm max-w-none text-on-surface-variant space-y-4 leading-relaxed">
          {children}
        </div>
      </div>
    </div>
  );
}

export function TermsPage() {
  return (
    <LegalPage title="Terms of Service">
      <p>
        By using Daffodil Intelligence you agree to use the platform responsibly for academic guidance
        and related university services.
      </p>
      <p>
        You are responsible for keeping your account credentials secure and for activity under your account.
      </p>
      <p>
        We may update these terms from time to time. Continued use of the service after changes constitutes
        acceptance of the updated terms.
      </p>
    </LegalPage>
  );
}

export function PrivacyPage() {
  return (
    <LegalPage title="Privacy Policy">
      <p>
        Daffodil Intelligence collects information you provide during registration, such as your name,
        email address, and usage data needed to deliver the service.
      </p>
      <p>
        We use your email for authentication, verification codes, and important account notifications.
        We do not sell your personal information to third parties.
      </p>
      <p>
        Contact your institution administrator if you have questions about data retention or account deletion.
      </p>
    </LegalPage>
  );
}
