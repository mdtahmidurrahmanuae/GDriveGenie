import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./contexts/**/*.{ts,tsx}",
    "./hooks/**/*.{ts,tsx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        brand: "#7c3aed",
        "gg-bg":      "var(--gg-bg)",
        "gg-s1":      "var(--gg-s1)",
        "gg-s2":      "var(--gg-s2)",
        "gg-border":  "var(--gg-border)",
        "gg-hover":   "var(--gg-hover)",
        "gg-text":    "var(--gg-text)",
        "gg-text2":   "var(--gg-text2)",
        "gg-text3":   "var(--gg-text3)",
        "gg-sidebar": "var(--gg-sidebar)",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "-apple-system", "sans-serif"],
      },
      keyframes: {
        float: {
          "0%, 100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(-10px)" },
        },
        fadeUp: {
          from: { opacity: "0", transform: "translateY(24px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
        fadeIn: {
          from: { opacity: "0" },
          to: { opacity: "1" },
        },
        gradientShift: {
          "0%, 100%": { backgroundPosition: "0% 50%" },
          "50%": { backgroundPosition: "100% 50%" },
        },
      },
      animation: {
        float: "float 4s ease-in-out infinite",
        "float-slow": "float 6s ease-in-out infinite",
        "float-delayed": "float 5s ease-in-out 1s infinite",
        "fade-up": "fadeUp 0.6s ease forwards",
        "fade-up-d1": "fadeUp 0.6s 0.1s ease forwards both",
        "fade-up-d2": "fadeUp 0.6s 0.2s ease forwards both",
        "fade-up-d3": "fadeUp 0.6s 0.3s ease forwards both",
        "fade-up-d4": "fadeUp 0.6s 0.4s ease forwards both",
        "fade-in": "fadeIn 0.4s ease forwards",
        "gradient-shift": "gradientShift 5s ease infinite",
      },
      backdropBlur: {
        xs: "2px",
      },
    },
  },
  plugins: [],
};

export default config;
