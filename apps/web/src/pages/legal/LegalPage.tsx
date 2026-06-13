import { PublicLayout } from "@layout";
import { PUBLIC_LAYOUT_WIDTH } from "@lib";

interface LegalPageProps {
  title: string;
  children: React.ReactNode;
}

function LegalPage({ title, children }: LegalPageProps) {
  return (
    <PublicLayout>
      <main className={`${PUBLIC_LAYOUT_WIDTH} flex-1 py-10 sm:py-16 animate-fadeIn`}>
        <div className="max-w-2xl">
          <h1 className="mb-4 text-3xl font-medium">{title}</h1>
          <div className="prose prose-sm max-w-none space-y-4 leading-relaxed text-on-surface-variant">
            {children}
          </div>
        </div>
      </main>
    </PublicLayout>
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
