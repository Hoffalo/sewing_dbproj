import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "var(--bg)",
        surface: "var(--surface)",
        ink: {
          DEFAULT: "var(--ink)",
          soft: "var(--ink-soft)",
        },
        lavender: {
          50: "var(--lavender-50)",
          100: "var(--lavender-100)",
          200: "var(--lavender-200)",
          300: "var(--lavender-300)",
          400: "var(--lavender-400)",
          500: "var(--lavender-500)",
          600: "var(--lavender-600)",
          700: "var(--lavender-700)",
        },
      },
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      boxShadow: {
        glow: "0 0 32px rgba(139,109,240,0.25), 0 0 8px rgba(139,109,240,0.15)",
        "glow-lg":
          "0 0 60px rgba(139,109,240,0.30), 0 0 20px rgba(139,109,240,0.18)",
        soft: "0 1px 2px rgba(26,21,48,0.04), 0 8px 24px rgba(26,21,48,0.05)",
      },
      borderRadius: {
        xl: "14px",
        "2xl": "20px",
      },
    },
  },
  plugins: [],
} satisfies Config;
