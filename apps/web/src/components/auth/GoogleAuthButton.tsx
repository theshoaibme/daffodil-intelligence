import React, { useEffect, useState } from "react";
import { fetchGoogleOAuthConfig, googleOAuthStartUrl } from "@lib";
import { Button } from "../ui";
import { ROUTES } from "@lib";

interface GoogleAuthButtonProps {
  disabled?: boolean;
  className?: string;
}

const MUTED_BUTTON_CLASS =
  "!bg-surface-container-high !text-on-surface border border-outline-variant/30 hover:!bg-surface-container-high disabled:!opacity-100";

export const GoogleAuthButton: React.FC<GoogleAuthButtonProps> = ({ disabled, className = "" }) => {
  const [redirecting, setRedirecting] = useState(false);
  const [enabled, setEnabled] = useState(false);
  const [configLoading, setConfigLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    fetchGoogleOAuthConfig()
      .then((config) => {
        if (!cancelled) setEnabled(Boolean(config.enabled));
      })
      .catch(() => {
        if (!cancelled) setEnabled(false);
      })
      .finally(() => {
        if (!cancelled) setConfigLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, []);

  const isDisabled = disabled || !enabled || configLoading;

  const handleClick = () => {
    if (redirecting || isDisabled) return;
    setRedirecting(true);
    window.location.href = googleOAuthStartUrl();
  };

  return (
    <Button
      type="button"
      variant="tonal"
      size="lg"
      loading={redirecting || configLoading}
      loadingDiameter={24}
      loadingStrokeWidth={2.5}
      className={`w-full ${MUTED_BUTTON_CLASS} ${className}`}
      disabled={isDisabled}
      onClick={handleClick}
      title={enabled ? "Continue with Google" : undefined}
    >
      <span className="inline-flex items-center justify-center gap-3">
        <GoogleIcon />
        <span className={isDisabled && !configLoading ? "text-on-surface-variant/80" : undefined}>
          Continue with Google
        </span>
      </span>
    </Button>
  );
};

function GoogleIcon() {
  return (
    <svg
      width="20"
      height="20"
      viewBox="0 0 18 18"
      aria-hidden="true"
      className="shrink-0"
    >
      <path
        fill="#4285F4"
        d="M17.64 9.2c0-.637-.057-1.251-.164-1.84H9v3.481h4.844a4.14 4.14 0 0 1-1.796 2.716v2.259h2.908c3.4-3.137 5.338-7.757 5.338-13.216z"
      />
      <path
        fill="#34A853"
        d="M9 18c2.43 0 4.467-.806 5.956-2.18l-2.908-2.259c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332A8.997 8.997 0 0 0 9 18z"
      />
      <path
        fill="#FBBC05"
        d="M3.964 10.71A5.41 5.41 0 0 1 3.682 9c0-.593.102-1.17.282-1.71V4.958H.957A8.997 8.997 0 0 0 0 9c0 1.452.348 2.827.957 4.042l3.007-2.332z"
      />
      <path
        fill="#EA4335"
        d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0A8.997 8.997 0 0 0 .957 4.958L3.964 7.29C4.672 5.163 6.656 3.58 9 3.58z"
      />
    </svg>
  );
}

/** Legacy redirect URI for direct code exchange (prefer server OAuth flow). */
function googleRedirectUri(): string {
  return `${window.location.origin}${ROUTES.googleCallback}`;
}

export { googleRedirectUri };
