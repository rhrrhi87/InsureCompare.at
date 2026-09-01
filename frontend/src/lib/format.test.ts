// File: frontend/src/lib/format.test.ts
import { describe, expect, it } from "vitest";

import { formatBytes, formatEur, formatPercent, formatScore } from "./format";

describe("formatEur", () => {
  it("formats Austrian euros", () => {
    expect(formatEur(70)).toMatch(/70/);
    expect(formatEur(70)).toMatch(/€/);
  });

  it("returns em-dash for null/undefined", () => {
    expect(formatEur(null)).toBe("—");
    expect(formatEur(undefined)).toBe("—");
  });
});

describe("formatPercent", () => {
  it("multiplies by 100", () => {
    expect(formatPercent(0.78)).toBe("78%");
  });

  it("respects fractionDigits", () => {
    expect(formatPercent(0.7842, 1)).toBe("78.4%");
  });
});

describe("formatScore", () => {
  it("rounds to nearest integer string", () => {
    expect(formatScore(94.4)).toBe("94");
    expect(formatScore(94.6)).toBe("95");
  });
});

describe("formatBytes", () => {
  it("renders bytes / KB / MB", () => {
    expect(formatBytes(512)).toBe("512 B");
    expect(formatBytes(1500)).toBe("1.5 KB");
    expect(formatBytes(2_500_000)).toBe("2.4 MB");
  });
});
