import React, { useState, useEffect, useRef } from "react";
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
  const [isVisible, setIsVisible] = useState(true);
  const lastScrollY = useRef(0);

  useEffect(() => {
    const handleScroll = () => {
      const currentScrollY = window.scrollY;

      // Always show header at the very top of the page
      if (currentScrollY < 50) {
        setIsVisible(true);
        lastScrollY.current = currentScrollY;
        return;
      }

      // Check distance to avoid hyper-sensitivity/jitter
      const scrollDiff = Math.abs(currentScrollY - lastScrollY.current);
      if (scrollDiff < 10) {
        return;
      }

      if (currentScrollY > lastScrollY.current) {
        // Scrolling down -> hide header
        setIsVisible(false);
      } else {
        // Scrolling up -> show header
        setIsVisible(true);
      }

      lastScrollY.current = currentScrollY;
    };

    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <div className="min-h-screen bg-background text-on-surface font-sans flex flex-col animate-fadeIn">
      {/* Centered navigation header with dynamic smart-sticky transition */}
      <header className={`sticky top-0 z-[60] bg-surface-container-lowest/90 backdrop-blur-md shrink-0 w-full transition-all duration-300 ease-in-out ${
        isVisible ? "translate-y-0 opacity-100" : "-translate-y-full opacity-0 pointer-events-none"
      }`}>
        <div className="max-w-[90rem] mx-auto w-full px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-6 sm:gap-10">
            <Logo size="md" />
            <nav className="hidden sm:flex items-center gap-5 sm:gap-7">
              {/* Researchs dropdown */}
              <div className="relative group">
                <Link
                  to={ROUTES.publicResearchs}
                  className="text-sm font-medium text-on-surface-variant hover:text-on-surface transition-colors flex items-center gap-1"
                >
                  Researchs
                  <svg width="12" height="12" viewBox="0 0 12 12" fill="none" className="mt-px opacity-60 transition-transform duration-200 group-hover:rotate-180">
                    <path d="M3 4.5L6 7.5L9 4.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                </Link>

                {/* Dropdown — full width */}
                <div className="fixed left-0 right-0 top-[64px] pt-0 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-[70]">
                  <div className="shadow-xl px-6 py-5 bg-surface-container-lowest">
                    <div className="max-w-[90rem] mx-auto">
                      <Link
                        to={ROUTES.publicResearchs}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold text-primary hover:bg-primary/10 transition-colors mb-3"
                      >
                        All Research
                      </Link>
                      <div className="h-px bg-outline-variant/10 mb-3" />
                      <div className="grid grid-cols-3 gap-x-6 gap-y-0.5">
                        {[
                          "Computer Science",
                          "Artificial Intelligence",
                          "Machine Learning",
                          "Natural Language Processing",
                          "Computer Vision",
                          "Deep Learning",
                          "Data Science",
                          "AI & Education",
                          "Smart Grids",
                          "Cybersecurity",
                          "Bioinformatics",
                          "Quantum Computing",
                          "Robotics",
                          "Cloud Computing",
                          "Internet of Things",
                          "Blockchain",
                          "Human-Computer Interaction",
                          "Software Engineering",
                        ].map((cat) => (
                          <Link
                            key={cat}
                            to={`${ROUTES.publicResearchs}?category=${encodeURIComponent(cat)}`}
                            className="group/item flex items-center justify-between px-3 py-2 rounded-lg text-xs text-on-surface-variant hover:bg-surface-container-low hover:text-on-surface transition-all"
                          >
                            {cat}
                            <svg
                              width="10" height="10" viewBox="0 0 10 10" fill="none"
                              className="opacity-0 translate-x-1 group-hover/item:opacity-60 group-hover/item:translate-x-0 transition-all duration-150 shrink-0"
                            >
                              <path d="M3.5 2L7 5L3.5 8" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                            </svg>
                          </Link>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              </div>

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
