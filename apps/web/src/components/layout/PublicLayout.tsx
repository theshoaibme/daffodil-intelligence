import React from "react";
import { Link } from "react-router-dom";
import { Logo } from "../logo";
import { UserMenu } from "./UserMenu";
import { useAuth } from "@context";
import { ROUTES } from "@lib";

interface PublicLayoutProps {
  children: React.ReactNode;
}

export function PublicLayout({ children }: PublicLayoutProps) {
  const { isAuthenticated, isLoading } = useAuth();

  return (
    <div className="min-h-screen bg-background text-on-surface font-sans flex flex-col animate-fadeIn">
      {/* Centered navigation header */}
      <header className="sticky top-0 z-[60] bg-surface-container-lowest/90 backdrop-blur-md shrink-0 w-full">
        <div className="max-w-[90rem] mx-auto w-full px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-6 sm:gap-10">
            <Logo size="md" />
            <nav className="hidden sm:flex items-center gap-5 sm:gap-7">
              <Link
                to={ROUTES.publicResearchs}
                className="text-sm font-medium text-on-surface-variant hover:text-on-surface transition-colors"
              >
                Researchs
              </Link>
              <Link
                to={ROUTES.connections}
                className="text-sm font-medium text-on-surface-variant hover:text-on-surface transition-colors"
              >
                Connections
              </Link>
            </nav>
          </div>

          {!isLoading && (
            <nav className="flex items-center gap-2 sm:gap-4">
              {isAuthenticated ? (
                <UserMenu signOutRedirect={ROUTES.landing} showWorkspaceLink />
              ) : (
                <>
                  <Link
                    to={ROUTES.login}
                    className="px-4 py-2 text-sm font-medium text-on-surface-variant hover:text-on-surface rounded-xl transition-colors"
                  >
                    Sign in
                  </Link>
                  <Link
                    to={ROUTES.register}
                    className="px-5 py-2.5 text-sm font-medium bg-primary text-on-primary rounded-full hover:opacity-90 transition-opacity"
                  >
                    Get started
                  </Link>
                </>
              )}
            </nav>
          )}
        </div>
      </header>

      {/* Children pages manage their own inner container margins/widths */}
      {children}
    </div>
  );
}
