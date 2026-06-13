import React, { useState, useEffect, useRef, useCallback } from "react";
import { Link } from "react-router-dom";
import { Logo } from "../logo";
import { PublicFooter } from "./PublicFooter";
import { UserMenu } from "./UserMenu";
import { useAuth } from "@context";
import { PUBLIC_LAYOUT_WIDTH, ROUTES } from "@lib";
import { useResearchCategories } from "../../pages/research/hooks/useResearchCategories";

interface PublicLayoutProps {
  children: React.ReactNode;
}

const CLOSE_DELAY_MS = 150;

const navLinkClass =
  "text-[15px] font-semibold text-on-surface hover:text-primary transition-colors";

export function PublicLayout({ children }: PublicLayoutProps) {
  const { isAuthenticated, isLoading } = useAuth();
  const { categories: researchCategories } = useResearchCategories();
  const [isVisible, setIsVisible] = useState(true);
  const [researchOpen, setResearchOpen] = useState(false);
  const lastScrollY = useRef(0);
  const closeTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    const handleScroll = () => {
      const currentScrollY = window.scrollY;

      if (currentScrollY < 50) {
        setIsVisible(true);
        lastScrollY.current = currentScrollY;
        return;
      }

      const scrollDiff = Math.abs(currentScrollY - lastScrollY.current);
      if (scrollDiff < 10) {
        return;
      }

      if (currentScrollY > lastScrollY.current) {
        setIsVisible(false);
        setResearchOpen(false);
      } else {
        setIsVisible(true);
      }

      lastScrollY.current = currentScrollY;
    };

    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  useEffect(() => {
    return () => {
      if (closeTimerRef.current) clearTimeout(closeTimerRef.current);
    };
  }, []);

  const openResearch = useCallback(() => {
    if (closeTimerRef.current) {
      clearTimeout(closeTimerRef.current);
      closeTimerRef.current = null;
    }
    setResearchOpen(true);
  }, []);

  const scheduleCloseResearch = useCallback(() => {
    if (closeTimerRef.current) clearTimeout(closeTimerRef.current);
    closeTimerRef.current = setTimeout(() => {
      setResearchOpen(false);
      closeTimerRef.current = null;
    }, CLOSE_DELAY_MS);
  }, []);

  const closeResearchNow = useCallback(() => {
    if (closeTimerRef.current) clearTimeout(closeTimerRef.current);
    setResearchOpen(false);
  }, []);

  return (
    <div className="min-h-screen bg-background text-on-surface font-sans flex flex-col animate-fadeIn">
      <header className="sticky top-0 z-[60] w-full shrink-0 overflow-visible">
        <div
          className={`bg-background w-full overflow-visible transition-all duration-300 ease-in-out ${
            isVisible ? "translate-y-0 opacity-100" : "-translate-y-full opacity-0 pointer-events-none"
          }`}
        >
          <div className={`${PUBLIC_LAYOUT_WIDTH} relative h-16 flex items-center justify-between overflow-visible`}>
            <div className="flex items-center shrink-0">
              <Logo size="md" />
            </div>

            <nav className="hidden md:flex absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 items-center gap-5 lg:gap-7 overflow-visible">
              {/* Single hover zone: trigger + full-width panel are siblings */}
              <div
                className="relative overflow-visible"
                onMouseEnter={openResearch}
                onMouseLeave={scheduleCloseResearch}
              >
                <Link
                  to={ROUTES.publicResearchs}
                  className={`${navLinkClass} flex items-center gap-1 py-4`}
                >
                  Researchs
                  <svg
                    width="12"
                    height="12"
                    viewBox="0 0 12 12"
                    fill="none"
                    className={`mt-px opacity-80 transition-transform duration-200 ${researchOpen ? "rotate-180" : ""}`}
                  >
                    <path
                      d="M3 4.5L6 7.5L9 4.5"
                      stroke="currentColor"
                      strokeWidth="1.5"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                </Link>

                <div
                  className={`absolute left-1/2 top-full z-[70] w-screen max-w-[100vw] -translate-x-1/2 transition-all duration-200 ${
                    researchOpen && isVisible
                      ? "opacity-100 visible pointer-events-auto"
                      : "opacity-0 invisible pointer-events-none"
                  }`}
                >
                  {/* Invisible bridge — keeps hover alive between link and panel */}
                  <div className="h-3" aria-hidden />
                  <div className="w-full bg-background shadow-md border-outline-variant/10 px-6 py-5">
                    <div className={PUBLIC_LAYOUT_WIDTH}>
                      <Link
                        to={ROUTES.publicResearchs}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold text-primary hover:bg-primary/10 transition-colors mb-3"
                        onClick={closeResearchNow}
                      >
                        All Research
                      </Link>
                      <div className="h-px bg-outline-variant/10 mb-3" />
                      <div className="grid grid-cols-3 gap-x-6 gap-y-0.5">
                        {researchCategories.map((cat) => (
                          <Link
                            key={cat}
                            to={`${ROUTES.publicResearchs}?category=${encodeURIComponent(cat)}`}
                            className="group/item flex items-center justify-between px-3 py-2 rounded-lg text-xs text-on-surface-variant hover:bg-surface-container-low hover:text-on-surface transition-all"
                            onClick={closeResearchNow}
                          >
                            {cat}
                            <svg
                              width="10"
                              height="10"
                              viewBox="0 0 10 10"
                              fill="none"
                              className="opacity-0 translate-x-1 group-hover/item:opacity-60 group-hover/item:translate-x-0 transition-all duration-150 shrink-0"
                            >
                              <path
                                d="M3.5 2L7 5L3.5 8"
                                stroke="currentColor"
                                strokeWidth="1.5"
                                strokeLinecap="round"
                                strokeLinejoin="round"
                              />
                            </svg>
                          </Link>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <Link to={ROUTES.publicConnections} className={navLinkClass}>
                Connections
              </Link>

              <Link to={ROUTES.pricing} className={navLinkClass}>
                Pricing
              </Link>

              <Link to={ROUTES.home} className={navLinkClass}>
                Studio
              </Link>
            </nav>

            {!isLoading && (
              <nav className="flex items-center gap-2 sm:gap-4 shrink-0">
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
        </div>
      </header>

      <div className="flex flex-1 flex-col">{children}</div>
      <PublicFooter />
    </div>
  );
}
