// File: frontend/src/lib/format.ts

const eurFormatter = new Intl.NumberFormat("de-AT", {
  style: "currency",
  currency: "EUR",
  maximumFractionDigits: 2,
});

const eurFormatterCompact = new Intl.NumberFormat("de-AT", {
  style: "currency",
  currency: "EUR",
  notation: "compact",
  maximumFractionDigits: 1,
});

export function formatEur(value: number | null | undefined): string {
  if (value === null || value === undefined) return "—";
  return eurFormatter.format(value);
}

export function formatEurCompact(value: number | null | undefined): string {
  if (value === null || value === undefined) return "—";
  return eurFormatterCompact.format(value);
}

export function formatPercent(value: number, fractionDigits = 0): string {
  return `${(value * 100).toFixed(fractionDigits)}%`;
}

export function formatScore(value: number): string {
  return Math.round(value).toString();
}

/** Returns a 1-decimal kilobyte / megabyte representation. */
export function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}
