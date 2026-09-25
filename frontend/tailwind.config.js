/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        // A restrained slate/blue palette — professional SOC-tool feel,
        // not a neon "hacker" theme. Status colors are muted, not garish.
        surface: {
          950: "#0a0e14",
          900: "#0f1420",
          800: "#151b2b",
          700: "#1e2638",
          600: "#2a3348",
        },
        accent: {
          400: "#5b9dd9",
          500: "#3d7ebf",
          600: "#2f66a3",
        },
        status: {
          success: "#4a9d6e",
          warning: "#c99a3a",
          danger: "#c0524a",
          info: "#4a7fb5",
          neutral: "#6b7280",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "ui-monospace", "monospace"],
      },
    },
  },
  plugins: [],
};
