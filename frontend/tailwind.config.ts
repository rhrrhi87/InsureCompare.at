import type { Config } from "tailwindcss";

// File: frontend/tailwind.config.ts
const config: Config = {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50:  "#eff6ff",
          100: "#dbeafe",
          200: "#bfdbfe",
          300: "#93c5fd",
          400: "#60a5fa",
          500: "#3b82f6",
          600: "#2563eb",   // primary CTA blue (matches prototype "Sign In" / "Get Started")
          700: "#1d4ed8",
          800: "#1e40af",
          900: "#1e3a8a",
        },
        accent: {
          // Used on best-match card and highlighted scores
          DEFAULT: "#1d4ed8",
          dark:    "#1e3a8a",
        },
        risk: {
          low:    "#16a34a",
          medium: "#ca8a04",
          high:   "#dc2626",
        },
      },
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "Segoe UI", "Helvetica", "Arial"],
      },
      boxShadow: {
        card: "0 4px 12px -2px rgb(15 23 42 / 0.08), 0 2px 4px -2px rgb(15 23 42 / 0.04)",
        elevated: "0 12px 24px -8px rgb(15 23 42 / 0.15)",
      },
      borderRadius: {
        xl: "0.875rem",
        "2xl": "1.25rem",
      },
    },
  },
  plugins: [],
};

export default config;
