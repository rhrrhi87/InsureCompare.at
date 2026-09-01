// File: frontend/src/components/ui/ProviderLogo.tsx
import { useState } from "react";

import { cn } from "@/lib/cn";
import type { Provider } from "@/types/domain";

/**
 * Renders a provider's real, official logo (see docs/DATA_PROVENANCE_AUDIT.md
 * for the sourced logo_url table). The image is hotlinked from the
 * insurer's own domain, not stored in this repository. Falls back to a
 * neutral initial badge if the URL is missing or fails to load — third-party
 * assets we don't control can break at any time, and the UI must degrade
 * honestly rather than showing a broken-image icon. `object-contain` inside
 * a fixed-size box preserves the logo's own aspect ratio regardless of its
 * native dimensions (logos here range from 100px to 1276px wide).
 */
export function ProviderLogo({
  provider,
  size = 24,
  className,
}: {
  provider: Provider;
  size?: number;
  className?: string;
}) {
  const [failed, setFailed] = useState(false);

  if (!provider.logo_url || failed) {
    return (
      <span
        data-testid="provider-logo-fallback"
        className={cn(
          "inline-flex shrink-0 items-center justify-center rounded-full bg-slate-200 font-semibold text-slate-600",
          className,
        )}
        style={{ width: size, height: size, fontSize: size * 0.5 }}
        aria-hidden="true"
      >
        {provider.name.charAt(0)}
      </span>
    );
  }

  return (
    <img
      data-testid="provider-logo-image"
      src={provider.logo_url}
      alt={provider.name}
      title={provider.name}
      className={cn("shrink-0 rounded bg-white object-contain p-0.5 ring-1 ring-slate-200", className)}
      style={{ width: size, height: size }}
      loading="lazy"
      onError={() => setFailed(true)}
    />
  );
}
