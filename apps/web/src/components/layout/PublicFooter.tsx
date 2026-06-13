import { Link } from "react-router-dom";
import { Logo } from "../logo";
import { PUBLIC_LAYOUT_WIDTH, ROUTES } from "@lib";

export function PublicFooter() {
  return (
    <footer className="mt-auto shrink-0 border-t border-outline-variant/30 py-10 lg:py-12">
      <div className={PUBLIC_LAYOUT_WIDTH}>
        <div className="flex flex-col items-center justify-between gap-6 sm:flex-row">
          <Logo size="sm" />
          <nav className="flex flex-wrap items-center justify-center gap-4 text-sm text-on-surface-variant sm:gap-6">
            <Link to={ROUTES.terms} className="transition-colors hover:text-on-surface">
              Terms
            </Link>
            <Link to={ROUTES.privacy} className="transition-colors hover:text-on-surface">
              Privacy
            </Link>
            <Link to={ROUTES.contacts} className="transition-colors hover:text-on-surface">
              Contact
            </Link>
            <Link to={ROUTES.login} className="transition-colors hover:text-on-surface">
              Sign in
            </Link>
          </nav>
          <span className="text-sm text-on-surface-variant">
            © {new Date().getFullYear()} Daffodil Intelligence
          </span>
        </div>
      </div>
    </footer>
  );
}
